#!/usr/bin/env python3
"""Checkpoint skill entry."""
import os
import sys
import tempfile
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
import narrate


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

    index_path = sl.data_session_dir(root, thread_id) / "INDEX.md"
    fm = io.read_frontmatter(index_path) or {}
    last_offset = int(fm.get("last_processed_offset", 0))

    delta, new_offset = jp.extract_delta(str(jsonl), last_offset)

    schema_path = SCRIPTS / "narration_schema.json"
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as t:
        out_path = Path(t.name)
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

    print(
        "Checkpoint saved: "
        f"{len(delta)} turns -> {result_path.context_path.relative_to(Path(root))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
