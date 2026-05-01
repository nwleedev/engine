#!/usr/bin/env python3
"""Checkpoint skill entry."""
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dotenv_loader
import project_root as pr
import session_locator as sl
import jsonl_parser as jp
import index_io as io
import narrate


def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.strip())
    return safe[:60].strip("-") or "checkpoint"


def _render_context(r: dict) -> str:
    lines = [f"# {r['title']}", "", "## 무엇을/왜", r["what_why"], "", "## 결정"]
    for d in r.get("decisions") or []:
        lines.append(f"- {d}")
    lines.extend(["", "## 미완료"])
    for o in r.get("open") or []:
        lines.append(f"- {o}")
    lines.extend(["", "## 다음", r["next"], ""])
    return "\n".join(lines)


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
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "contexts").mkdir(exist_ok=True)
    index_path = session_dir / "INDEX.md"

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

    title = result["title"]
    now = datetime.now().strftime("%Y%m%d-%H%M")
    ctx_filename = f"CONTEXT-{now}-{_slug(title)}.md"
    ctx_path = session_dir / "contexts" / ctx_filename
    ctx_path.write_text(_render_context(result))

    if not index_path.exists():
        io.write_index(index_path, frontmatter={
            "session_id": thread_id,
            "cwd": cwd,
            "started": _now_iso(),
            "last_updated": _now_iso(),
            "last_processed_offset": new_offset,
            "jsonl_path": str(jsonl),
        }, contexts=[])

    summary = (result["what_why"] or "").splitlines()[0][:120]
    io.append_context_entry(index_path, filename=ctx_filename, summary=summary)
    io.update_frontmatter(index_path, last_processed_offset=new_offset, last_updated=_now_iso())

    print(f"Checkpoint saved: {len(delta)} turns -> .codex/sessions/{thread_id[:8]}/contexts/{ctx_filename}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
