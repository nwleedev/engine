#!/usr/bin/env python3
"""Move legacy child session directories into flat session-memory artifacts."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
import re
import shutil
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
LEGACY_CHILD_SESSIONS_DIR = "_children"
FLAT_THREADS_RELATIVE_PATH = "session-memory/threads"
EXIT_OPERATION_FAILED = 2
MOVE_ERRORS = (OSError, shutil.Error)
RELATIONSHIP_SOURCE_FIELDS = {"role", "parent_session_id"}


@dataclass
class MigrationCandidate:
    source: Path
    parent_id: str | None


@dataclass
class MovedSession:
    destination: Path
    source: Path
    parent_id: str | None
    original_index_text: str | None


@dataclass(frozen=True)
class IndexBackup:
    path: Path
    text: str


def _load_script_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, HERE / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


pl = _load_script_module("parent_locator.py", "codex_session_memory_migrate_parent_locator")
sl = _load_script_module("session_locator.py", "codex_session_memory_migrate_session_locator")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Move legacy child session directories under "
            ".codex/session-memory/threads."
        )
    )
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--apply", action="store_true", help="Move sessions instead of printing a dry-run.")
    return parser.parse_args(argv)


def _sessions_root(project_root: Path) -> Path:
    return project_root / ".codex" / "sessions"


def _candidate_dirs(sessions_root: Path) -> list[Path]:
    if not sessions_root.is_dir():
        return []
    candidates = []
    legacy_children_root = sessions_root / LEGACY_CHILD_SESSIONS_DIR
    if legacy_children_root.is_dir():
        for path in sorted(legacy_children_root.iterdir(), key=lambda item: item.name):
            if not path.is_dir():
                continue
            if path.name.startswith((".", "_")):
                continue
            if not (path / "INDEX.md").is_file():
                continue
            candidates.append(path)

    for path in sorted(sessions_root.iterdir(), key=lambda item: item.name):
        if not path.is_dir():
            continue
        if path.name.startswith((".", "_")):
            continue
        if not (path / "INDEX.md").is_file():
            continue
        candidates.append(path)
    return candidates


def _find_rollout_path(thread_id: str):
    finder = getattr(sl, "find_jsonl_by_thread", None)
    if not callable(finder):
        return None
    return finder(thread_id)


def _parse_frontmatter(index_path: Path) -> dict[str, str]:
    try:
        text = index_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", len("---"))
    if end < 0:
        return {}

    frontmatter: dict[str, str] = {}
    for line in text[len("---") : end].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip("\"'")
    return frontmatter


def _frontmatter_parent_id(candidate: Path) -> str | None:
    frontmatter = _parse_frontmatter(candidate / "INDEX.md")
    if frontmatter.get("role") != "child":
        return None
    parent_session_id = frontmatter.get("parent_session_id")
    if parent_session_id:
        return parent_session_id
    return None


def _migration_candidates(
    project_root: Path,
    candidates: list[Path],
) -> list[MigrationCandidate]:
    migratable = []
    for candidate in candidates:
        thread_id = candidate.name
        rollout_path = _find_rollout_path(thread_id)
        resolution = pl.resolve_parent_thread_id(
            thread_id,
            rollout_path=rollout_path,
            codex_home=project_root / ".codex",
        )
        if resolution.role == "child" and resolution.parent_thread_id:
            migratable.append(
                MigrationCandidate(candidate, str(resolution.parent_thread_id))
            )
            continue
        parent_session_id = _frontmatter_parent_id(candidate)
        migratable.append(MigrationCandidate(candidate, parent_session_id))
    return migratable


def _print_manual_cleanup_required(message: str, paths: list[Path]) -> None:
    joined_paths = ", ".join(str(path) for path in paths)
    print(f"MANUAL CLEANUP REQUIRED: {message}: {joined_paths}", file=sys.stderr)


def _destination_path(project_root: Path, child_id: str) -> Path:
    return project_root / ".codex" / FLAT_THREADS_RELATIVE_PATH / child_id


def _has_destination_conflicts(
    project_root: Path,
    migratable: list[MigrationCandidate],
) -> bool:
    conflicts = []
    seen_destinations: set[Path] = set()
    for candidate in migratable:
        child_id = candidate.source.name
        destination = _destination_path(project_root, child_id)
        if destination.exists():
            conflicts.append((child_id, destination, "destination exists"))
        elif destination in seen_destinations:
            conflicts.append((child_id, destination, "duplicate destination"))
        seen_destinations.add(destination)

    for child_id, destination, reason in conflicts:
        print(f"CONFLICT {child_id}: {reason} at {destination}", file=sys.stderr)
    return bool(conflicts)


def _apply_migration(project_root: Path, source: Path, parent_id: str | None) -> None:
    child_id = source.name
    destination = _destination_path(project_root, child_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def _write_text_atomically(path: Path, text: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    try:
        temp_path.write_text(text, encoding="utf-8")
        temp_path.replace(path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _restore_moved_index_text(moved_session: MovedSession) -> bool:
    if moved_session.original_index_text is None:
        return True
    index_path = moved_session.destination / "INDEX.md"
    if not index_path.exists():
        return True
    try:
        _write_text_atomically(index_path, moved_session.original_index_text)
        return True
    except OSError as exc:
        print(f"ERROR rollback failed for {index_path}: {exc}", file=sys.stderr)
        _print_manual_cleanup_required(
            "restore original INDEX.md content manually",
            [index_path],
        )
        return False


def _rollback_moved_sessions(moved: list[MovedSession]) -> bool:
    rolled_back = True
    for moved_session in reversed(moved):
        if not _restore_moved_index_text(moved_session):
            rolled_back = False
        destination = moved_session.destination
        source = moved_session.source
        try:
            shutil.move(str(destination), str(source))
            print(f"ROLLBACK {destination.name}: restored source", file=sys.stderr)
        except MOVE_ERRORS as exc:
            rolled_back = False
            print(
                f"ERROR rollback failed for {destination} -> {source}: {exc}",
                file=sys.stderr,
            )
            _print_manual_cleanup_required(
                "move child session back to source manually",
                [destination, source],
            )
    return rolled_back


def _cleanup_created_artifacts_root(artifacts_root: Path, existed_before_apply: bool) -> bool:
    if existed_before_apply or not artifacts_root.exists():
        return True
    try:
        artifacts_root.rmdir()
        return True
    except OSError as exc:
        print(f"ERROR cleanup failed for {artifacts_root}: {exc}", file=sys.stderr)
        _print_manual_cleanup_required(
            "remove empty session-memory/threads directory if appropriate",
            [artifacts_root],
        )
        return False


def _print_committed_moves(moved: list[MovedSession]) -> None:
    for moved_session in moved:
        child_id = moved_session.destination.name
        parent_label = moved_session.parent_id or "none"
        print(
            f"MOVED {child_id} -> "
            f"{FLAT_THREADS_RELATIVE_PATH}/{child_id} parent={parent_label}"
        )


def _strip_relationship_frontmatter_fields(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", len("---\n"))
    if end < 0:
        return text

    frontmatter_text = text[len("---\n") : end]
    body = text[end + len("\n---") :]
    lines = frontmatter_text.splitlines()
    kept_lines = []
    for line in lines:
        key, separator, _value = line.partition(":")
        if separator and key.strip() in RELATIONSHIP_SOURCE_FIELDS:
            continue
        kept_lines.append(line)
    return "---\n" + "\n".join(kept_lines) + "\n---" + body


def _normalize_destination_index(destination: Path) -> tuple[bool, str | None]:
    index_path = destination / "INDEX.md"
    try:
        original_text = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR reading migrated INDEX.md for {destination.name}: {exc}", file=sys.stderr)
        return False, None

    normalized_text = _strip_relationship_frontmatter_fields(original_text)
    if normalized_text == original_text:
        return True, original_text
    try:
        _write_text_atomically(index_path, normalized_text)
        return True, original_text
    except OSError as exc:
        print(f"ERROR normalizing migrated INDEX.md for {destination.name}: {exc}", file=sys.stderr)
        return False, original_text


def _parent_index_path(project_root: Path, parent_id: str, moved_by_id: dict[str, Path]) -> Path:
    moved_parent = moved_by_id.get(parent_id)
    if moved_parent is not None:
        return moved_parent / "INDEX.md"
    return project_root / ".codex" / "sessions" / parent_id / "INDEX.md"


def _remove_legacy_child_link_lines(text: str, child_ids: set[str]) -> str:
    if not child_ids:
        return text
    link_targets = "|".join(
        re.escape(f"../{LEGACY_CHILD_SESSIONS_DIR}/{child_id}/INDEX.md")
        for child_id in sorted(child_ids)
    )
    synthetic_link_line = re.compile(
        rf"^[ \t]*-[ \t]*\[[^\]\n]*\]\((?:{link_targets})\)"
        rf"[ \t]*-[ \t]*migrated child session[ \t]*(?:\r?\n)?$"
    )
    legacy_link_token = re.compile(rf"\[[^\]\n]*\]\((?:{link_targets})\)")
    cleaned_lines = []
    for line in text.splitlines(keepends=True):
        if synthetic_link_line.match(line):
            continue
        cleaned_lines.append(legacy_link_token.sub("", line))
    return "".join(cleaned_lines)


def _cleanup_parent_legacy_links(
    project_root: Path,
    moved: list[MovedSession],
) -> tuple[bool, list[IndexBackup]]:
    child_ids_by_parent: dict[str, set[str]] = {}
    moved_by_id = {session.destination.name: session.destination for session in moved}
    for moved_session in moved:
        if not moved_session.parent_id:
            continue
        child_ids_by_parent.setdefault(moved_session.parent_id, set()).add(
            moved_session.destination.name
        )

    backups = []
    for parent_id, child_ids in sorted(child_ids_by_parent.items()):
        index_path = _parent_index_path(project_root, parent_id, moved_by_id)
        if not index_path.is_file():
            continue
        try:
            original_text = index_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR reading parent INDEX.md for {parent_id}: {exc}", file=sys.stderr)
            return False, backups
        cleaned_text = _remove_legacy_child_link_lines(original_text, child_ids)
        if cleaned_text == original_text:
            continue
        backups.append(IndexBackup(index_path, original_text))
        try:
            _write_text_atomically(index_path, cleaned_text)
        except OSError as exc:
            print(f"ERROR cleaning parent INDEX.md for {parent_id}: {exc}", file=sys.stderr)
            return False, backups
    return True, backups


def _restore_index_backups(backups: list[IndexBackup]) -> bool:
    restored = True
    for backup in reversed(backups):
        try:
            _write_text_atomically(backup.path, backup.text)
        except OSError as exc:
            restored = False
            print(f"ERROR rollback failed for {backup.path}: {exc}", file=sys.stderr)
            _print_manual_cleanup_required(
                "restore parent INDEX.md content manually",
                [backup.path],
            )
    return restored


def _apply_with_rollback(
    project_root: Path,
    migratable: list[MigrationCandidate],
    artifacts_root_existed_before_apply: bool,
) -> bool:
    moved: list[MovedSession] = []
    parent_backups: list[IndexBackup] = []
    artifacts_root = project_root / ".codex" / FLAT_THREADS_RELATIVE_PATH
    for candidate in migratable:
        source = candidate.source
        child_id = source.name
        destination = _destination_path(project_root, child_id)
        try:
            _apply_migration(project_root, source, candidate.parent_id)
        except MOVE_ERRORS as exc:
            print(f"ERROR moving {child_id}: {exc}", file=sys.stderr)
            _restore_index_backups(parent_backups)
            _rollback_moved_sessions(moved)
            _cleanup_created_artifacts_root(
                artifacts_root,
                artifacts_root_existed_before_apply,
            )
            return False
        moved.append(MovedSession(destination, source, candidate.parent_id, None))
        normalized, original_text = _normalize_destination_index(destination)
        moved[-1].original_index_text = original_text
        if not normalized:
            _restore_index_backups(parent_backups)
            _rollback_moved_sessions(moved)
            _cleanup_created_artifacts_root(
                artifacts_root,
                artifacts_root_existed_before_apply,
            )
            return False

    parent_links_cleaned, parent_backups = _cleanup_parent_legacy_links(
        project_root,
        moved,
    )
    if not parent_links_cleaned:
        _restore_index_backups(parent_backups)
        _rollback_moved_sessions(moved)
        _cleanup_created_artifacts_root(
            artifacts_root,
            artifacts_root_existed_before_apply,
        )
        return False

    _print_committed_moves(moved)
    return True


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    project_root = Path(args.root).resolve()
    if not project_root.is_dir():
        print(f"error: root does not exist: {project_root}", file=sys.stderr)
        return 2

    migratable = _migration_candidates(
        project_root,
        _candidate_dirs(_sessions_root(project_root)),
    )
    if not args.apply:
        for candidate in migratable:
            child_id = candidate.source.name
            parent_label = candidate.parent_id or "none"
            print(
                f"DRY-RUN {child_id} -> "
                f"{FLAT_THREADS_RELATIVE_PATH}/{child_id} parent={parent_label}"
            )
        return 0

    if _has_destination_conflicts(project_root, migratable):
        return EXIT_OPERATION_FAILED

    artifacts_root_existed_before_apply = (
        project_root / ".codex" / FLAT_THREADS_RELATIVE_PATH
    ).exists()
    if not _apply_with_rollback(
        project_root,
        migratable,
        artifacts_root_existed_before_apply,
    ):
        return EXIT_OPERATION_FAILED
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
