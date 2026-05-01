#!/usr/bin/env python3
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dotenv_loader
import project_root as pr
import session_locator as sl
import jsonl_parser as jp
import index_io as io


def main():
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)

    thread_id = sl.current_thread_id()
    if not thread_id:
        print("CODEX_THREAD_ID: not set (run inside a Codex session)")
        return 0

    root = pr.find_project_root(cwd)
    session_dir = sl.data_session_dir(root, thread_id)
    index_path = session_dir / "INDEX.md"
    jsonl = sl.find_jsonl_by_thread(thread_id)

    print(f"thread_id: {thread_id}")
    print(f"project_root: {root}")
    print(f"session_dir: {session_dir}")
    print(f"jsonl: {jsonl or '(not found)'}")

    if not index_path.exists():
        print("status: not yet checkpointed")
        return 0

    fm = io.read_frontmatter(index_path) or {}
    last_offset = int(fm.get("last_processed_offset", 0))
    pending = 0
    if jsonl and jsonl.is_file():
        delta, _ = jp.extract_delta(str(jsonl), last_offset)
        pending = len(delta)

    contexts_dir = session_dir / "contexts"
    ctx_count = len(list(contexts_dir.glob("CONTEXT-*.md"))) if contexts_dir.is_dir() else 0

    print(f"started: {fm.get('started', '?')}")
    print(f"last_updated: {fm.get('last_updated', '?')}")
    print(f"contexts: {ctx_count} file(s)")
    print(f"pending_turns: {pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
