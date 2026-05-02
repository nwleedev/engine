#!/usr/bin/env python3
import importlib.util
import os
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
csm_jsonl_parser = _load_script_module(
    "jsonl_parser.py", "codex_session_memory_status_jsonl_parser"
)
csm_index_io = _load_script_module(
    "index_io.py", "codex_session_memory_status_index_io"
)


def main():
    cwd = os.getcwd()
    csm_dotenv_loader.load_project_dotenv(cwd)

    thread_id = csm_session_locator.current_thread_id()
    if not thread_id:
        print("CODEX_THREAD_ID: not set (run inside a Codex session)")
        return 0

    root = csm_project_root.find_project_root(cwd)
    session_dir = csm_session_locator.data_session_dir(root, thread_id)
    index_path = session_dir / "INDEX.md"
    jsonl = csm_session_locator.find_jsonl_by_thread(thread_id)
    contexts_dir = session_dir / "contexts"
    ctx_count = len(list(contexts_dir.glob("CONTEXT-*.md"))) if contexts_dir.is_dir() else 0

    print(f"Project root: {root}")
    print(f"Thread id: {thread_id}")
    print(f"JSONL path: {jsonl or 'missing'}")

    if not index_path.exists():
        print(f"Context files: {ctx_count}")
        print("Last saved: never")
        print("Pending offset: 0")
        print("Hooks: SessionStart, Stop, PostToolUse")
        print("status: not yet checkpointed")
        return 0

    fm = csm_index_io.read_frontmatter(index_path) or {}
    last_offset = int(fm.get("last_processed_offset", 0))
    pending = 0
    if jsonl and jsonl.is_file():
        delta, _ = csm_jsonl_parser.extract_delta(str(jsonl), last_offset)
        pending = len(delta)

    print(f"Context files: {ctx_count}")
    print(f"Last saved: {fm.get('last_updated') or 'never'}")
    print(f"Pending offset: {last_offset}")
    print("Hooks: SessionStart, Stop, PostToolUse")
    print(f"started: {fm.get('started', '?')}")
    print(f"pending_turns: {pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
