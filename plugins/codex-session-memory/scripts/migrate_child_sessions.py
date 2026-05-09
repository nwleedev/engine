#!/usr/bin/env python3
"""Move legacy top-level child session directories under _children."""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
CHILD_SESSIONS_DIR = "_children"
CHILD_SESSIONS_HEADING = "## Child Sessions"
EXIT_OPERATION_FAILED = 2
MOVE_ERRORS = (OSError, shutil.Error)


@dataclass(frozen=True)
class ParentIndexUpdate:
    original_text: str
    updated_text: str


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
        description="Move top-level child session directories under .codex/sessions/_children."
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


def _migratable_sessions(candidates: list[Path]) -> list[tuple[Path, str]]:
    migratable = []
    for candidate in candidates:
        thread_id = candidate.name
        rollout_path = _find_rollout_path(thread_id)
        resolution = pl.resolve_parent_thread_id(thread_id, rollout_path=rollout_path)
        if resolution.role == "child" and resolution.parent_thread_id:
            migratable.append((candidate, str(resolution.parent_thread_id)))
            continue
        parent_session_id = _frontmatter_parent_id(candidate)
        if parent_session_id:
            migratable.append((candidate, parent_session_id))
    return migratable


def _child_link_target(child_id: str) -> str:
    return f"../_children/{child_id}/INDEX.md"


def _child_link(child_id: str) -> str:
    return f"- [{child_id[:8]}]({_child_link_target(child_id)}) - migrated child session"


def _updated_parent_index_text(text: str, child_id: str) -> str:
    if _child_link_target(child_id) in text:
        return text

    link = _child_link(child_id)
    lines = text.splitlines()
    try:
        heading_index = lines.index(CHILD_SESSIONS_HEADING)
    except ValueError:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend([CHILD_SESSIONS_HEADING, "", link])
    else:
        insert_at = heading_index + 1
        if insert_at < len(lines) and lines[insert_at] == "":
            insert_at += 1
        while insert_at < len(lines) and lines[insert_at].startswith("- ["):
            insert_at += 1
        lines.insert(insert_at, link)

    return "\n".join(lines) + "\n"


def _parent_index_path(project_root: Path, parent_id: str) -> Path:
    return _sessions_root(project_root) / parent_id / "INDEX.md"


def _prepare_parent_index_updates(
    project_root: Path,
    migratable: list[tuple[Path, str]],
) -> dict[Path, ParentIndexUpdate] | None:
    updates: dict[Path, ParentIndexUpdate] = {}
    for source, parent_id in migratable:
        child_id = source.name
        parent_index = _parent_index_path(project_root, parent_id)
        if not parent_index.is_file():
            print(f"WARNING parent INDEX.md missing for {parent_id}", file=sys.stderr)
            continue
        try:
            update = updates.get(parent_index)
            if update is None:
                text = parent_index.read_text(encoding="utf-8")
                original_text = text
            else:
                text = update.updated_text
                original_text = update.original_text
            updated_text = _updated_parent_index_text(text, child_id)
        except OSError as exc:
            print(
                f"ERROR parent INDEX.md update unavailable for {parent_id}: {exc}",
                file=sys.stderr,
            )
            return None
        if updated_text != text or parent_index in updates:
            updates[parent_index] = ParentIndexUpdate(
                original_text=original_text,
                updated_text=updated_text,
            )
    return updates


def _print_manual_cleanup_required(message: str, paths: list[Path]) -> None:
    joined_paths = ", ".join(str(path) for path in paths)
    print(f"MANUAL CLEANUP REQUIRED: {message}: {joined_paths}", file=sys.stderr)


def _restore_parent_index_updates(
    written: list[Path],
    updates: dict[Path, ParentIndexUpdate],
) -> bool:
    restored = True
    for parent_index in reversed(written):
        try:
            parent_index.write_text(updates[parent_index].original_text, encoding="utf-8")
        except OSError as exc:
            restored = False
            print(
                f"ERROR rollback failed for parent INDEX.md {parent_index}: {exc}",
                file=sys.stderr,
            )
            _print_manual_cleanup_required(
                "restore parent INDEX.md manually",
                [parent_index],
            )
    return restored


def _write_parent_index_updates(updates: dict[Path, ParentIndexUpdate]) -> bool:
    written = []
    for parent_index, update in updates.items():
        try:
            parent_index.write_text(update.updated_text, encoding="utf-8")
        except OSError as exc:
            print(
                f"ERROR parent INDEX.md update failed for {parent_index}: {exc}",
                file=sys.stderr,
            )
            _restore_parent_index_updates(written, updates)
            return False
        written.append(parent_index)
    return True


def _destination_path(project_root: Path, child_id: str) -> Path:
    return _sessions_root(project_root) / CHILD_SESSIONS_DIR / child_id


def _has_destination_conflicts(project_root: Path, migratable: list[tuple[Path, str]]) -> bool:
    conflicts = []
    for source, _parent_id in migratable:
        child_id = source.name
        destination = _destination_path(project_root, child_id)
        if destination.exists():
            conflicts.append((child_id, destination))

    for child_id, destination in conflicts:
        print(f"CONFLICT {child_id}: destination exists at {destination}", file=sys.stderr)
    return bool(conflicts)


def _apply_migration(project_root: Path, source: Path, parent_id: str) -> None:
    child_id = source.name
    children_root = _sessions_root(project_root) / CHILD_SESSIONS_DIR
    destination = _destination_path(project_root, child_id)
    children_root.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def _rollback_moved_children(moved: list[tuple[Path, Path, str]]) -> bool:
    rolled_back = True
    for destination, source, _parent_id in reversed(moved):
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


def _cleanup_created_children_root(children_root: Path, existed_before_apply: bool) -> bool:
    if existed_before_apply or not children_root.exists():
        return True
    try:
        children_root.rmdir()
        return True
    except OSError as exc:
        print(f"ERROR cleanup failed for {children_root}: {exc}", file=sys.stderr)
        _print_manual_cleanup_required(
            "remove empty _children directory if appropriate",
            [children_root],
        )
        return False


def _print_committed_moves(moved: list[tuple[Path, Path, str]]) -> None:
    for destination, _source, parent_id in moved:
        child_id = destination.name
        print(f"MOVED {child_id} -> _children/{child_id} parent={parent_id}")


def _apply_with_rollback(
    project_root: Path,
    migratable: list[tuple[Path, str]],
    parent_updates: dict[Path, ParentIndexUpdate],
    children_root_existed_before_apply: bool,
) -> bool:
    moved: list[tuple[Path, Path, str]] = []
    children_root = _sessions_root(project_root) / CHILD_SESSIONS_DIR
    for source, parent_id in migratable:
        child_id = source.name
        destination = _destination_path(project_root, child_id)
        try:
            _apply_migration(project_root, source, parent_id)
        except MOVE_ERRORS as exc:
            print(f"ERROR moving {child_id}: {exc}", file=sys.stderr)
            _rollback_moved_children(moved)
            _cleanup_created_children_root(children_root, children_root_existed_before_apply)
            return False
        moved.append((destination, source, parent_id))

    if _write_parent_index_updates(parent_updates):
        _print_committed_moves(moved)
        return True

    _rollback_moved_children(moved)
    _cleanup_created_children_root(children_root, children_root_existed_before_apply)
    return False


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    project_root = Path(args.root).resolve()
    if not project_root.is_dir():
        print(f"error: root does not exist: {project_root}", file=sys.stderr)
        return 2

    migratable = _migratable_sessions(_candidate_dirs(_sessions_root(project_root)))
    if not args.apply:
        for source, parent_id in migratable:
            child_id = source.name
            print(f"DRY-RUN {child_id} -> _children/{child_id} parent={parent_id}")
        return 0

    if _has_destination_conflicts(project_root, migratable):
        return EXIT_OPERATION_FAILED

    parent_updates = _prepare_parent_index_updates(project_root, migratable)
    if parent_updates is None:
        return EXIT_OPERATION_FAILED

    children_root_existed_before_apply = (
        _sessions_root(project_root) / CHILD_SESSIONS_DIR
    ).exists()
    if not _apply_with_rollback(
        project_root,
        migratable,
        parent_updates,
        children_root_existed_before_apply,
    ):
        return EXIT_OPERATION_FAILED
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
