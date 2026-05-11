#!/usr/bin/env python3
"""Prepare and verify Codex session memory checkpoint handoffs."""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"


def _load_script_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


dotenv_loader = _load_script_module(
    "dotenv_loader.py", "codex_session_memory_checkpoint_dotenv_loader"
)
ee = _load_script_module(
    "evidence_extractor.py", "codex_session_memory_checkpoint_evidence_extractor"
)
io = _load_script_module("index_io.py", "codex_session_memory_checkpoint_index_io")
jp = _load_script_module("jsonl_parser.py", "codex_session_memory_checkpoint_jsonl_parser")
pl = _load_script_module("parent_locator.py", "codex_session_memory_parent_locator")
pr = _load_script_module("project_root.py", "codex_session_memory_checkpoint_project_root")
sl = _load_script_module(
    "session_locator.py", "codex_session_memory_checkpoint_session_locator"
)


REQUIRED_SECTIONS = (
    "## current_goal",
    "## executive_summary",
    "## detailed_state",
    "## decisions",
    "## files",
    "## verification",
    "## risks",
    "## next_actions",
    "## graph_context",
)


def _usage() -> str:
    return (
        "usage: checkpoint.py prepare [--role main|child] [--parent <session-id>] | "
        "checkpoint.py verify <context-path>"
    )


def _print_usage() -> None:
    print(_usage(), file=sys.stderr)


def _resolve_project_root(cwd: str) -> str | None:
    try:
        root = pr.find_project_root(cwd)
        pr.assert_root_is_canonical(root, cwd)
    except Exception as exc:
        print(f"error: project root validation failed: {exc}", file=sys.stderr)
        return None
    return root


def _data_session_dir(root: str, thread_id: str, role: str) -> Path:
    try:
        return sl.data_session_dir(root, thread_id, role=role)
    except TypeError:
        if role == "main":
            return sl.data_session_dir(root, thread_id)
        raise


def _artifact_session_dir(root: str, thread_id: str) -> Path:
    if hasattr(sl, "artifact_session_dir"):
        return sl.artifact_session_dir(root, thread_id)
    return Path(root) / ".codex" / "session-memory" / "threads" / thread_id


def _coerce_offset(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _suggest_context_path(contexts_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H00")
    return contexts_dir / f"CONTEXT-{stamp}-checkpoint.md"


def _render_list(items: list[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def _render_evidence(evidence: dict) -> str:
    return "\n".join(
        [
            "### files",
            _render_list(evidence.get("files", [])),
            "",
            "### commands",
            _render_list(evidence.get("commands", [])),
            "",
            "### failures",
            _render_list(evidence.get("failures", [])),
            "",
            "### sources",
            _render_list(evidence.get("sources", [])),
        ]
    )


def _is_context_path_in_session_tree(context_path: Path, root: str) -> bool:
    sessions_root = (Path(root) / ".codex" / "sessions").resolve()
    artifact_threads_root = (
        Path(root) / ".codex" / "session-memory" / "threads"
    ).resolve()
    try:
        relative = context_path.relative_to(artifact_threads_root)
    except ValueError:
        pass
    else:
        if len(relative.parts) == 3 and relative.parts[1] == "contexts":
            return not relative.parts[0].startswith(("_", "."))
        return False

    try:
        relative = context_path.relative_to(sessions_root)
    except ValueError:
        return False
    if len(relative.parts) == 3 and relative.parts[1] == "contexts":
        return not relative.parts[0].startswith(("_", "."))
    return (
        len(relative.parts) == 4
        and relative.parts[0] == "_children"
        and relative.parts[2] == "contexts"
    )


def _contains_required_heading_lines(context_text: str) -> str | None:
    lines = set(context_text.splitlines())
    for section in REQUIRED_SECTIONS:
        if section not in lines:
            return section
    return None


def _index_has_context_entry(index_text: str, filename: str) -> bool:
    entry_re = re.compile(rf"^\s*-\s+\[{re.escape(filename)}\](?:\s|$)")
    return any(entry_re.match(line) for line in index_text.splitlines())


def _parse_prepare_args(args: list[str]) -> tuple[str | None, str | None] | None:
    role = None
    parent = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--role":
            if i + 1 >= len(args):
                print("error: --role requires main or child", file=sys.stderr)
                return None
            role = args[i + 1]
            i += 2
            continue
        if arg == "--parent":
            if i + 1 >= len(args):
                print("error: --parent requires <session-id>", file=sys.stderr)
                return None
            parent = args[i + 1]
            i += 2
            continue
        print(f"error: unknown prepare argument: {arg}", file=sys.stderr)
        return None
    if role is not None and role not in {"main", "child"}:
        print("error: --role must be main or child", file=sys.stderr)
        return None
    return role, parent


def _prepare_retry_guidance() -> str:
    return "retry with --parent <session-id> or set CODEX_SESSION_PARENT_ID"


def _resolve_prepare_target(
    *,
    requested_role: str | None,
    requested_parent: str | None,
    thread_id: str,
    jsonl_path: Path | None,
    project_root: str | Path,
) -> tuple[str, str | None] | None:
    if requested_parent:
        if requested_role == "main":
            print("error: --parent conflicts with --role main", file=sys.stderr)
            return None
        return "child", requested_parent

    env_parent = os.environ.get("CODEX_SESSION_PARENT_ID")
    if env_parent:
        if requested_role == "main":
            print("error: CODEX_SESSION_PARENT_ID conflicts with --role main", file=sys.stderr)
            return None
        return "child", env_parent

    resolution = pl.resolve_parent_thread_id(
        thread_id=thread_id,
        rollout_path=jsonl_path,
        codex_home=Path(project_root) / ".codex",
    )
    if resolution.role == "child":
        if requested_role == "main":
            print(
                "error: --role main conflicts with detected child checkpoint metadata",
                file=sys.stderr,
            )
            return None
        if resolution.parent_thread_id:
            return "child", resolution.parent_thread_id
        print(
            f"error: child checkpoint detected without parent session id; {_prepare_retry_guidance()}",
            file=sys.stderr,
        )
        return None

    if requested_role == "child":
        print(
            f"error: child checkpoint requested but no parent session id was found; {_prepare_retry_guidance()}",
            file=sys.stderr,
        )
        return None

    return "main", None


def _prepare(requested_role: str | None = None, requested_parent: str | None = None) -> int:
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)

    thread_id = sl.current_thread_id()
    if not thread_id:
        print("error: CODEX_THREAD_ID is required for checkpoint prepare", file=sys.stderr)
        return 2

    root = _resolve_project_root(cwd)
    if root is None:
        return 2

    jsonl_path = sl.find_jsonl_by_thread(thread_id)

    resolved = _resolve_prepare_target(
        requested_role=requested_role,
        requested_parent=requested_parent,
        thread_id=thread_id,
        jsonl_path=jsonl_path,
        project_root=root,
    )
    if resolved is None:
        return 2
    role, parent_session_id = resolved

    if not jsonl_path:
        print(f"error: no rollout JSONL found for thread {thread_id}", file=sys.stderr)
        return 2

    session_dir = _artifact_session_dir(root, thread_id)
    index_path = session_dir / "INDEX.md"
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    parent_index_path = None

    frontmatter = io.read_frontmatter(index_path) or {}
    last_processed_offset = _coerce_offset(frontmatter.get("last_processed_offset", 0))
    delta, new_offset = jp.extract_delta(str(jsonl_path), last_processed_offset)
    context_path = _suggest_context_path(contexts_dir)
    evidence = ee.extract_evidence(delta)

    print(
        "\n".join(
            [
                "# checkpoint prepare",
                "",
                "The active Codex must write the context file and update INDEX.md.",
                "",
                "## target",
                f"thread_id: {thread_id}",
                f"role: {role}",
                f"parent_session_id: {parent_session_id or ''}",
                f"project_root: {root}",
                f"jsonl_path: {jsonl_path}",
                f"index_path: {index_path}",
                f"context_path: {context_path}",
                f"parent_index_path: {parent_index_path or ''}",
                f"previous_processed_offset: {last_processed_offset}",
                f"new_offset: {new_offset}",
                "",
                "## index update",
                f"index_entry: - [{context_path.name}] — <summary>",
                "parent_child_entry:",
                "frontmatter_update:",
                f"  last_processed_offset: {new_offset}",
                "  last_updated: <ISO-8601 timestamp>",
                "  session_id: <thread_id>",
                "",
                "relationship_diagnostics:",
                "  relationship_source: codex graph",
                f"  detected_role: {role}",
                f"  detected_parent_session_id: {parent_session_id or ''}",
                "",
                "## evidence",
                _render_evidence(evidence),
                "",
                "## required context template",
                "# <title>",
                "",
                *REQUIRED_SECTIONS,
                "",
                "After writing the context, update INDEX.md to reference the context filename.",
                "Set INDEX.md frontmatter last_processed_offset to the printed new offset.",
            ]
        )
    )
    return 0


def _verify(context_arg: str) -> int:
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)
    root = _resolve_project_root(cwd)
    if root is None:
        return 2

    context_path = Path(context_arg)
    if not context_path.is_absolute():
        context_path = Path(root) / context_path
    context_path = context_path.resolve()

    if not _is_context_path_in_session_tree(context_path, root):
        print(
            f"error: context path is outside project session contexts: {context_path}",
            file=sys.stderr,
        )
        return 1

    if not context_path.is_file():
        print(f"error: context file does not exist: {context_path}", file=sys.stderr)
        return 1

    context_text = context_path.read_text(encoding="utf-8")
    missing_section = _contains_required_heading_lines(context_text)
    if missing_section:
        print(f"error: missing section: {missing_section}", file=sys.stderr)
        return 1

    index_path = context_path.parent.parent / "INDEX.md"
    if not index_path.is_file():
        print(f"error: INDEX.md does not exist: {index_path}", file=sys.stderr)
        return 1

    index_text = index_path.read_text(encoding="utf-8")
    if not _index_has_context_entry(index_text, context_path.name):
        print(
            f"error: INDEX.md does not include context entry for {context_path.name}",
            file=sys.stderr,
        )
        return 1

    print("verify: ok")
    return 0


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if not args:
        _print_usage()
        return 2

    command = args[0]
    if command == "prepare":
        parsed = _parse_prepare_args(args)
        if parsed is None:
            _print_usage()
            return 2
        requested_role, requested_parent = parsed
        return _prepare(requested_role=requested_role, requested_parent=requested_parent)
    if command == "verify" and len(args) == 2:
        return _verify(args[1])

    _print_usage()
    return 2


if __name__ == "__main__":
    sys.exit(main())
