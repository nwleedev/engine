#!/usr/bin/env python3
"""Prepare and verify Codex session memory checkpoint handoffs."""
from __future__ import annotations

import importlib.util
import os
import re
import secrets
import sys
from datetime import datetime, timezone
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
pr = _load_script_module("project_root.py", "codex_session_memory_checkpoint_project_root")
sl = _load_script_module(
    "session_locator.py", "codex_session_memory_checkpoint_session_locator"
)
artifact_store = _load_script_module(
    "artifact_store.py", "codex_session_memory_checkpoint_artifact_store"
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

CONTEXT_TEMPLATE_GUIDANCE = (
    ("## current_goal", "Capture the approved current goal and scope."),
    ("## executive_summary", "Write 3-7 lines that make the state resumable."),
    ("## detailed_state", "Record workflow, judgments, and confirmed facts."),
    ("## decisions", "List decisions, rationale, alternatives, and fallback."),
    ("## files", "Record per-file change reason and next check point."),
    (
        "## verification",
        "Record commands, results, failure causes, and unverified items.",
    ),
    ("## risks", "List remaining risks and uncertain assumptions."),
    ("## next_actions", "Record ordered steps the next person can run immediately."),
    (
        "## graph_context",
        "Record that Codex graph and parent discovery are not used; preserve source provenance.",
    ),
)


def _usage() -> str:
    return "usage: checkpoint.py prepare | checkpoint.py verify <context-path>"


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


def _coerce_offset(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _suggest_context_path(store, session_id: str, task_id: str, now_utc: datetime) -> Path:
    stamp = now_utc.strftime("%Y%m%d-%H%M%S")
    filename = store.context_filename(
        timestamp=stamp,
        task_id=task_id,
        nonce=secrets.token_hex(3),
    )
    return store.context_path(session_id, filename)


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


def _render_required_context_template(
    *,
    session_id: str,
    source_thread_id: str,
    task_id: str,
    checkpoint_id: str,
    created_at: str,
) -> str:
    lines = [
        "---",
        f"session_id: {session_id}",
        f"source_thread_id: {source_thread_id}",
        f"task_id: {task_id}",
        f"checkpoint_id: {checkpoint_id}",
        f"created_at: {created_at}",
        "---",
        "",
        "# <title>",
        "",
    ]
    for heading, guidance in CONTEXT_TEMPLATE_GUIDANCE:
        lines.extend([heading, f"- guidance: {guidance}", ""])
        if heading == "## graph_context":
            lines.extend(
                [
                    f"session_id: {session_id}",
                    f"source_thread_id: {source_thread_id}",
                    "graph_status: not_used",
                    "graph_source: none",
                    "",
                ]
            )
    return "\n".join(lines).rstrip()


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


def _parse_prepare_args(args: list[str]) -> bool:
    if len(args) == 1:
        return True
    print(f"error: unknown prepare argument: {args[1]}", file=sys.stderr)
    return False


def _prepare() -> int:
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)

    session_id = sl.current_session_id()
    if not session_id:
        print(
            "error: CODEX_SESSION_ID is required as the session-memory artifact target",
            file=sys.stderr,
        )
        return 2

    source_thread_id = sl.current_thread_id()
    if not source_thread_id:
        print("error: CODEX_THREAD_ID is required for checkpoint prepare", file=sys.stderr)
        return 2
    if source_thread_id != session_id:
        print(
            "warning: CODEX_THREAD_ID differs from CODEX_SESSION_ID; "
            "using CODEX_THREAD_ID only to read the rollout JSONL",
            file=sys.stderr,
        )

    root = _resolve_project_root(cwd)
    if root is None:
        return 2

    jsonl_path = sl.find_jsonl_by_thread(source_thread_id)
    if not jsonl_path:
        print(f"error: no rollout JSONL found for thread {source_thread_id}", file=sys.stderr)
        return 2

    store = artifact_store.ArtifactStore(root)
    index_path = store.index_path(session_id)

    frontmatter = io.read_frontmatter(index_path) or {}
    last_processed_offset = _coerce_offset(frontmatter.get("last_processed_offset", 0))
    delta, new_offset = jp.extract_delta(str(jsonl_path), last_processed_offset)
    now_utc = datetime.now(timezone.utc)
    task_id = "checkpoint"
    context_path = _suggest_context_path(store, session_id, task_id, now_utc)
    checkpoint_id = context_path.stem.removeprefix("CONTEXT-")
    created_at = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence = ee.extract_evidence(delta)
    context_text = _render_required_context_template(
        session_id=session_id,
        source_thread_id=source_thread_id,
        task_id=task_id,
        checkpoint_id=checkpoint_id,
        created_at=created_at,
    )

    print(
        "\n".join(
            [
                "# checkpoint prepare",
                "",
                "Preparing to write the context file and update INDEX.md.",
                "",
                "## target",
                f"session_id: {session_id}",
                f"source_thread_id: {source_thread_id}",
                f"project_root: {root}",
                f"jsonl_path: {jsonl_path}",
                f"index_path: {index_path}",
                f"context_path: {context_path}",
                f"previous_processed_offset: {last_processed_offset}",
                f"new_offset: {new_offset}",
                "",
                "## index update",
                f"index_entry: - [{context_path.name}] — <summary>",
                "frontmatter_update:",
                f"  last_processed_offset: {new_offset}",
                f"  last_updated: {created_at}",
                f"  session_id: {session_id}",
                f"  source_thread_id: {source_thread_id}",
                "",
                "## evidence",
                _render_evidence(evidence),
                "",
                "## required context template",
                context_text,
                "",
            ]
        )
    )

    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(context_text + "\n", encoding="utf-8")
    try:
        backup_path = io.append_context_entry_with_frontmatter(
            index_path,
            context_path.name,
            "<summary>",
            writer_id=checkpoint_id,
            session_id=session_id,
            source_thread_id=source_thread_id,
            artifact_schema_version=2,
            last_processed_offset=new_offset,
            last_updated=created_at,
        )
    except OSError as exc:
        backup_path = getattr(exc, "backup_path", None)
        backup_note = (
            f"; backup path: {backup_path}"
            if backup_path
            else "; no backup path was created before failure"
        )
        print(
            "error: INDEX.md update failed after context write; "
            f"context preserved at {context_path}{backup_note}; "
            "run session-memory status to find orphan contexts, then repair by "
            f"adding this entry under ## Contexts: - [{context_path.name}] — <summary>; "
            "also set frontmatter "
            f"last_processed_offset: {new_offset}, last_updated: {created_at}, "
            f"session_id: {session_id}, source_thread_id: {source_thread_id}; {exc}",
            file=sys.stderr,
        )
        return 1
    print("The active Codex wrote the context file and updated INDEX.md.")
    return 0


def _verify(context_arg: str) -> int:
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)
    session_id = sl.current_session_id()
    if not session_id:
        print(
            "error: CODEX_SESSION_ID is required as the session-memory artifact target",
            file=sys.stderr,
        )
        return 2

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
        if not _parse_prepare_args(args):
            _print_usage()
            return 2
        return _prepare()
    if command == "verify" and len(args) == 2:
        return _verify(args[1])

    _print_usage()
    return 2


if __name__ == "__main__":
    sys.exit(main())
