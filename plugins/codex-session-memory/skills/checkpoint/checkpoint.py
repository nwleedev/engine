#!/usr/bin/env python3
"""Checkpoint skill entry."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import context_writer
import dotenv_loader
import project_root as pr
import session_locator as sl
import jsonl_parser as jp
import index_io as io
import lockfile
import narrate


TEMP_SCOPE = Path("temps") / "2026-05-02" / "codex-session-memory-checkpoint"
LOCK_NAME = ".session-memory.lock"
LOCK_TIMEOUT_SECONDS = 5.0


def main():
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)

    thread_id = sl.current_thread_id()
    if not thread_id:
        print("error: CODEX_THREAD_ID not set. Run inside a Codex session.", file=sys.stderr)
        return 2

    root = pr.find_project_root(cwd)
    pr.assert_root_is_canonical(root, cwd)

    jsonl = sl.find_jsonl_by_thread(thread_id)
    if not jsonl:
        print(f"error: no rollout JSONL found for thread {thread_id[:8]}", file=sys.stderr)
        return 2

    session_dir = sl.data_session_dir(root, thread_id)
    lock_path = session_dir / LOCK_NAME
    temp_dir = Path(root) / TEMP_SCOPE
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_path = temp_dir / f"checkpoint-{thread_id[:8]}.json"
    try:
        with lockfile.acquire_lock(lock_path, timeout_seconds=LOCK_TIMEOUT_SECONDS):
            index_path = session_dir / "INDEX.md"
            fm = io.read_frontmatter(index_path) or {}
            last_offset = int(fm.get("last_processed_offset", 0))

            delta, new_offset = jp.extract_delta(str(jsonl), last_offset)

            schema_path = SCRIPTS / "narration_schema.json"
            try:
                prompt = narrate.build_prompt(
                    delta=delta or [{"role": "user", "text": "(no new turns; checkpoint marker only)"}]
                )
                result = narrate.call_codex_exec(prompt=prompt, schema_path=schema_path, out_path=out_path)
                narrate.validate(result)
            finally:
                try:
                    out_path.unlink()
                except OSError:
                    pass

            result_path = context_writer.write_context(
                project_root=Path(root),
                thread_id=thread_id,
                cwd=cwd,
                jsonl_path=str(jsonl),
                new_offset=new_offset,
                delta=delta,
                narration=result,
                reason="force",
            )
    except TimeoutError as exc:
        print(f"error: could not acquire session memory lock: {exc}", file=sys.stderr)
        return 1

    print(
        "Checkpoint saved: "
        f"{len(delta)} turns -> {result_path.context_path.relative_to(Path(root))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
