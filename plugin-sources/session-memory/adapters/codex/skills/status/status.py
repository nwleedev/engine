#!/usr/bin/env python3
import importlib.util
import os
import re
import sys
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


csm_dotenv_loader = _load_script_module(
    "dotenv_loader.py", "codex_session_memory_status_dotenv_loader"
)
csm_project_root = _load_script_module(
    "project_root.py", "codex_session_memory_status_project_root"
)
csm_session_locator = _load_script_module(
    "session_locator.py", "codex_session_memory_status_session_locator"
)
csm_index_io = _load_script_module(
    "index_io.py", "codex_session_memory_status_index_io"
)
csm_agents_rules = _load_script_module(
    "agents_rules.py", "codex_session_memory_status_agents_rules"
)


def _print_agents_rules_status(root):
    report = csm_agents_rules.check_agents_rules(root)
    print(f"AGENTS.md rules: {report.status}")
    if report.missing:
        print(f"AGENTS.md missing markers: {', '.join(report.missing)}")


def _artifact_session_dir(root, session_id):
    if hasattr(csm_session_locator, "artifact_session_dir"):
        return csm_session_locator.artifact_session_dir(root, session_id)
    return Path(root) / ".codex" / "session-memory" / "threads" / session_id


def _indexed_context_filenames(index_path):
    if not index_path.exists():
        return set()
    names = set()
    for match in re.finditer(r"^- \[([^\]]+)\]", index_path.read_text(encoding="utf-8"), re.MULTILINE):
        names.add(match.group(1))
    return names


def _orphan_context_paths(contexts_dir, index_path):
    if not contexts_dir.is_dir():
        return []
    indexed = _indexed_context_filenames(index_path)
    return [
        path
        for path in sorted(contexts_dir.glob("CONTEXT-*.md"), key=lambda item: item.name)
        if path.name not in indexed
    ]


def _print_orphan_context_diagnostics(contexts_dir, index_path):
    orphans = _orphan_context_paths(contexts_dir, index_path)
    print(f"Orphan contexts: {len(orphans)}")
    if not orphans:
        return
    print("Repair: add missing context entries to INDEX.md under ## Contexts.")
    for path in orphans:
        print(f"  - {path}")


def main():
    cwd = os.getcwd()
    csm_dotenv_loader.load_project_dotenv(cwd)

    session_id = csm_session_locator.current_session_id()
    if not session_id:
        print("CODEX_SESSION_ID: not set (session-memory artifact target is required)")
        return 0

    root = csm_project_root.find_project_root(cwd)
    session_dir = _artifact_session_dir(root, session_id)
    index_path = session_dir / "INDEX.md"
    contexts_dir = session_dir / "contexts"
    ctx_count = len(list(contexts_dir.glob("CONTEXT-*.md"))) if contexts_dir.is_dir() else 0

    print(f"Project root: {root}")
    print(f"Session id: {session_id}")
    print(f"Artifact path: {session_dir}")
    _print_agents_rules_status(root)

    if not index_path.exists():
        print(f"Artifact INDEX.md: missing ({index_path})")
        print(f"Context files: {ctx_count}")
        _print_orphan_context_diagnostics(contexts_dir, index_path)
        print("Last saved: never")
        print("Pending offset: 0")
        print("status: not yet checkpointed")
        return 0

    fm = csm_index_io.read_frontmatter(index_path) or {}
    last_offset = int(fm.get("last_processed_offset", 0))

    print(f"Context files: {ctx_count}")
    _print_orphan_context_diagnostics(contexts_dir, index_path)
    print(f"Last saved: {fm.get('last_updated') or 'never'}")
    print(f"Pending offset: {last_offset}")
    if "started" in fm:
        print(f"started: {fm.get('started')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
