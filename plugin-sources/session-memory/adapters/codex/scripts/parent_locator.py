"""Resolve Codex parent thread ids from rollout metadata and state DB files."""

from dataclasses import dataclass, field
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
from typing import Optional, Union
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

ROLLOUT_SCAN_LIMIT = 50


@dataclass(frozen=True)
class ParentResolution:
    role: str
    parent_thread_id: Optional[str] = None
    source: str = "none"
    confidence: str = "none"
    reason: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)


def resolve_parent_thread_id(
    thread_id: str,
    rollout_path: Optional[Union[str, Path]] = None,
    codex_home: Optional[Union[str, Path]] = None,
    sqlite_home: Optional[Union[str, Path]] = None,
) -> ParentResolution:
    """Return parent resolution evidence for the current Codex thread."""
    rollout_result = _from_rollout_session_meta(rollout_path)
    if rollout_result.parent_thread_id:
        return rollout_result

    db_result = _from_state_db(thread_id, codex_home=codex_home, sqlite_home=sqlite_home)
    warnings = rollout_result.warnings + db_result.warnings
    if db_result.parent_thread_id or db_result.role == "child":
        return _with_warnings(db_result, warnings)
    if rollout_result.role == "child":
        return _with_warnings(rollout_result, warnings)

    return ParentResolution(
        role="main",
        reason="no child evidence found",
        warnings=warnings,
    )


def _from_rollout_session_meta(
    rollout_path: Optional[Union[str, Path]]
) -> ParentResolution:
    if rollout_path is None:
        return ParentResolution(role="main", reason="rollout path missing")

    path = Path(rollout_path)
    if not path.is_file():
        return ParentResolution(role="main", reason="rollout file missing")

    warnings: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number in range(1, ROLLOUT_SCAN_LIMIT + 1):
                line = handle.readline()
                if not line:
                    break
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    warnings.append(f"malformed rollout json line {line_number}")
                    continue

                if item.get("type") != "session_meta":
                    continue

                source = _dict_get(item.get("payload"), "source")
                subagent = _dict_get(source, "subagent")
                thread_spawn = _dict_get(subagent, "thread_spawn")
                parent = thread_spawn.get("parent_thread_id")
                if parent:
                    return ParentResolution(
                        role="child",
                        parent_thread_id=str(parent),
                        source="rollout_session_meta",
                        confidence="high",
                        reason="session_meta contains subagent thread_spawn parent",
                        warnings=tuple(warnings),
                    )
                if subagent:
                    return ParentResolution(
                        role="child",
                        source="rollout_session_meta",
                        confidence="medium",
                        reason="session_meta contains subagent source without parent",
                        warnings=tuple(warnings),
                    )
    except OSError as exc:
        warnings.append(f"cannot read rollout file: {exc}")

    return ParentResolution(
        role="main",
        reason="session_meta child evidence missing",
        warnings=tuple(warnings),
    )


def _from_state_db(
    thread_id: str,
    *,
    codex_home: Optional[Union[str, Path]],
    sqlite_home: Optional[Union[str, Path]],
) -> ParentResolution:
    warnings: list[str] = []
    for db_path in _state_db_candidates(codex_home=codex_home, sqlite_home=sqlite_home):
        result = _from_state_db_path(thread_id, db_path)
        warnings.extend(result.warnings)
        if result.parent_thread_id or result.role == "child":
            return _with_warnings(result, tuple(warnings))

    return ParentResolution(
        role="main",
        reason="state db child evidence missing",
        warnings=tuple(warnings),
    )


def _state_db_candidates(
    *,
    codex_home: Optional[Union[str, Path]],
    sqlite_home: Optional[Union[str, Path]],
) -> list[Path]:
    homes: list[Path] = []
    for home in _sqlite_home_candidates(codex_home=codex_home, sqlite_home=sqlite_home):
        if home is None:
            continue
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
    codex_home: Optional[Union[str, Path]],
    sqlite_home: Optional[Union[str, Path]],
) -> list[Union[Path, str]]:
    homes: list[Union[Path, str]] = []
    if sqlite_home is not None:
        homes.append(sqlite_home)

    env_home = os.environ.get("CODEX_SQLITE_HOME", "").strip()
    if env_home:
        homes.append(Path(env_home).expanduser())

    configured = _configured_sqlite_home(codex_home)
    if configured is not None:
        homes.append(configured)

    if codex_home is not None:
        homes.append(codex_home)
    homes.append(Path.home() / ".codex")
    return homes


def _configured_sqlite_home(codex_home: Optional[Union[str, Path]]) -> Optional[Path]:
    config_homes: list[Path] = []
    if codex_home is not None:
        config_homes.append(Path(codex_home))
    default_home = Path.home() / ".codex"
    if default_home not in config_homes:
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


def _from_state_db_path(thread_id: str, db_path: Path) -> ParentResolution:
    warnings: list[str] = []
    try:
        conn = sqlite3.connect(_readonly_sqlite_uri(db_path), uri=True)
    except sqlite3.Error as exc:
        return ParentResolution(
            role="main",
            reason=f"cannot open state db {db_path.name}",
            warnings=(f"cannot open state db {db_path}: {exc}",),
        )

    try:
        edge_result = _from_thread_spawn_edges(conn, thread_id)
        if edge_result.parent_thread_id:
            return edge_result

        threads_result = _from_threads_source(conn, thread_id)
        warnings.extend(threads_result.warnings)
        if threads_result.parent_thread_id or threads_result.role == "child":
            return _with_warnings(threads_result, tuple(warnings))
    except sqlite3.Error as exc:
        warnings.append(f"cannot query state db {db_path}: {exc}")
    finally:
        conn.close()

    return ParentResolution(
        role="main",
        reason=f"state db {db_path.name} child evidence missing",
        warnings=tuple(warnings),
    )


def _from_thread_spawn_edges(conn: sqlite3.Connection, thread_id: str) -> ParentResolution:
    if not _table_has_columns(conn, "thread_spawn_edges", {"parent_thread_id", "child_thread_id"}):
        return ParentResolution(role="main", reason="thread_spawn_edges schema missing")

    row = conn.execute(
        "SELECT parent_thread_id FROM thread_spawn_edges WHERE child_thread_id = ? LIMIT 1",
        (thread_id,),
    ).fetchone()
    if row and row[0]:
        return ParentResolution(
            role="child",
            parent_thread_id=str(row[0]),
            source="state_db_thread_spawn_edges",
            confidence="high",
            reason="state db thread_spawn_edges matched child_thread_id",
        )
    return ParentResolution(role="main", reason="thread_spawn_edges child row missing")


def _from_threads_source(conn: sqlite3.Connection, thread_id: str) -> ParentResolution:
    if not _table_has_columns(conn, "threads", {"id", "source"}):
        return ParentResolution(role="main", reason="threads schema missing")

    row = conn.execute(
        "SELECT source FROM threads WHERE id = ? LIMIT 1",
        (thread_id,),
    ).fetchone()
    if not row or not row[0]:
        return ParentResolution(role="main", reason="threads source row missing")

    try:
        source = json.loads(row[0])
    except json.JSONDecodeError:
        return ParentResolution(
            role="main",
            reason="threads source json malformed",
            warnings=("malformed threads.source json",),
        )

    subagent = _dict_get(source, "subagent")
    thread_spawn = _dict_get(subagent, "thread_spawn")
    parent = thread_spawn.get("parent_thread_id")
    if parent:
        return ParentResolution(
            role="child",
            parent_thread_id=str(parent),
            source="state_db_threads_source",
            confidence="medium",
            reason="state db threads.source contains subagent thread_spawn parent",
        )
    if subagent:
        return ParentResolution(
            role="child",
            source="state_db_threads_source",
            confidence="low",
            reason="state db threads.source contains subagent source without parent",
        )
    return ParentResolution(role="main", reason="threads source child evidence missing")


def _table_has_columns(conn: sqlite3.Connection, table_name: str, columns: set[str]) -> bool:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    existing = {row[1] for row in rows}
    return columns.issubset(existing)


def _readonly_sqlite_uri(path: Path) -> str:
    return f"file:{quote(str(path.resolve()))}?mode=ro"


def _dict_get(value, key: str) -> dict:
    if not isinstance(value, dict):
        return {}
    next_value = value.get(key)
    if isinstance(next_value, dict):
        return next_value
    return {}


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _with_warnings(result: ParentResolution, warnings: tuple[str, ...]) -> ParentResolution:
    return ParentResolution(
        role=result.role,
        parent_thread_id=result.parent_thread_id,
        source=result.source,
        confidence=result.confidence,
        reason=result.reason,
        warnings=warnings,
    )
