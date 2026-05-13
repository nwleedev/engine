"""Read Codex thread graph edges from state DB files."""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import sqlite3
from urllib.parse import quote


def _load_toml_module():
    compat_path = Path(__file__).resolve().with_name("toml_compat.py")
    spec = importlib.util.spec_from_file_location("_session_memory_toml_compat", compat_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load TOML compatibility module from {compat_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_toml_module()


tomllib = _load_toml_module()

EDGE_COLUMNS = {"parent_thread_id", "child_thread_id"}
EDGE_STATUS_COLUMNS = EDGE_COLUMNS | {"status"}


@dataclass(frozen=True)
class ParentLookup:
    available: bool
    parent_thread_id: str | None = None


@dataclass(frozen=True)
class RoleLookup:
    role: str
    available: bool = True


class GraphStore:
    """Read parent/child relationships from Codex sqlite state."""

    def __init__(
        self,
        *,
        codex_home: str | Path | None = None,
        sqlite_home: str | Path | None = None,
        include_default_home: bool = True,
    ) -> None:
        self.codex_home = Path(codex_home).expanduser() if codex_home is not None else None
        self.sqlite_home = Path(sqlite_home).expanduser() if sqlite_home is not None else None
        self.include_default_home = include_default_home

    def parent_of(self, thread_id: str) -> ParentLookup:
        available = False
        for conn in self._connections(required_columns=EDGE_COLUMNS):
            available = True
            row = conn.execute(
                "SELECT parent_thread_id FROM thread_spawn_edges "
                "WHERE child_thread_id = ? LIMIT 1",
                (thread_id,),
            ).fetchone()
            if row and row[0]:
                return ParentLookup(available=True, parent_thread_id=str(row[0]))
        return ParentLookup(available=available)

    def children_of(self, parent_thread_id: str, status: str | None = None) -> list[str]:
        required_columns = EDGE_COLUMNS if status is None else EDGE_STATUS_COLUMNS
        for conn in self._connections(required_columns=required_columns):
            if status is None:
                rows = conn.execute(
                    "SELECT child_thread_id FROM thread_spawn_edges "
                    "WHERE parent_thread_id = ? ORDER BY child_thread_id ASC",
                    (parent_thread_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT child_thread_id FROM thread_spawn_edges "
                    "WHERE parent_thread_id = ? AND status = ? "
                    "ORDER BY child_thread_id ASC",
                    (parent_thread_id, status),
                ).fetchall()
            children = [str(row[0]) for row in rows if row and row[0]]
            if children:
                return children
        return []

    def descendants_of(self, root_thread_id: str) -> list[str]:
        descendants: list[str] = []
        current_level = sorted(self.children_of(root_thread_id))
        seen = set(current_level)

        while current_level:
            descendants.extend(current_level)
            next_level: set[str] = set()
            for thread_id in current_level:
                for child_id in self.children_of(thread_id):
                    if child_id in seen:
                        continue
                    seen.add(child_id)
                    next_level.add(child_id)
            current_level = sorted(next_level)

        return descendants

    def role_of(self, thread_id: str) -> RoleLookup:
        parent = self.parent_of(thread_id)
        if not parent.available:
            return RoleLookup(role="main", available=False)
        if parent.parent_thread_id:
            return RoleLookup(role="child", available=True)
        return RoleLookup(role="main", available=True)

    def _connections(self, *, required_columns: set[str]):
        for db_path in _state_db_candidates(
            codex_home=self.codex_home,
            sqlite_home=self.sqlite_home,
            include_default_home=self.include_default_home,
        ):
            try:
                conn = sqlite3.connect(_readonly_sqlite_uri(db_path), uri=True)
            except sqlite3.Error:
                continue

            try:
                if _table_has_columns(conn, "thread_spawn_edges", required_columns):
                    try:
                        yield conn
                    finally:
                        conn.close()
                    continue
            except sqlite3.Error:
                pass
            conn.close()


def _state_db_candidates(
    *,
    codex_home: str | Path | None,
    sqlite_home: str | Path | None,
    include_default_home: bool = True,
) -> list[Path]:
    homes: list[Path] = []
    for home in _sqlite_home_candidates(
        codex_home=codex_home,
        sqlite_home=sqlite_home,
        include_default_home=include_default_home,
    ):
        path = Path(home).expanduser()
        if path not in homes:
            homes.append(path)

    candidates: list[Path] = []
    for home in homes:
        if not home.is_dir():
            continue
        dbs = list(home.glob("state_*.sqlite"))
        if not dbs:
            continue
        preferred = home / "state_5.sqlite"
        if preferred in dbs:
            candidates.append(preferred)
            dbs = [path for path in dbs if path != preferred]
        candidates.extend(sorted(dbs, key=_state_db_sort_key, reverse=True))
    return candidates


def _sqlite_home_candidates(
    *,
    codex_home: str | Path | None,
    sqlite_home: str | Path | None,
    include_default_home: bool = True,
) -> list[Path | str]:
    homes: list[Path | str] = []
    if sqlite_home is not None:
        homes.append(sqlite_home)

    env_home = os.environ.get("CODEX_SQLITE_HOME", "").strip()
    if env_home:
        homes.append(Path(env_home).expanduser())

    configured = _configured_sqlite_home(
        codex_home,
        include_default_home=include_default_home,
    )
    if configured is not None:
        homes.append(configured)

    if codex_home is not None:
        homes.append(codex_home)
    if include_default_home:
        homes.append(Path.home() / ".codex")
    return homes


def _configured_sqlite_home(
    codex_home: str | Path | None,
    *,
    include_default_home: bool = True,
) -> Path | None:
    config_homes: list[Path] = []
    if codex_home is not None:
        config_homes.append(Path(codex_home))
    default_home = Path.home() / ".codex"
    if include_default_home and default_home not in config_homes:
        config_homes.append(default_home)

    for home in config_homes:
        config_path = home / "config.toml"
        if not config_path.is_file():
            continue
        try:
            data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        value = data.get("sqlite_home")
        if isinstance(value, str) and value.strip():
            path = Path(value).expanduser()
            if not path.is_absolute():
                path = config_path.parent / path
            return path
    return None


def _state_db_sort_key(path: Path) -> tuple[int, str]:
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        mtime_ns = -1
    return (mtime_ns, str(path))


def _table_has_columns(conn: sqlite3.Connection, table_name: str, columns: set[str]) -> bool:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    existing = {row[1] for row in rows}
    return columns.issubset(existing)


def _readonly_sqlite_uri(path: Path) -> str:
    return f"file:{quote(str(path.resolve()))}?mode=ro"


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'
