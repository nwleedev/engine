#!/usr/bin/env python3
"""PreToolUse hook: time/size-based periodic CONTEXT checkpoints."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import handwrite_context as hw

CHECKPOINT_INTERVAL = 300  # 5 minutes


def should_checkpoint(index_data, delta_text):
    """Returns True if time (>=5min) or size (>=80k chars) threshold exceeded."""
    if len(delta_text) >= hw.CHAR_LIMIT:
        return True
    last_written = index_data.get("last_context_written_at", "")
    if not last_written:
        return False
    try:
        last_dt = datetime.fromisoformat(last_written)
        elapsed = (datetime.utcnow() - last_dt).total_seconds()
        return elapsed >= CHECKPOINT_INTERVAL
    except Exception:
        return False


def main():
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        sys.exit(0)

    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")
    if not transcript_path or not session_id:
        sys.exit(0)

    cwd, messages = hw.parse_transcript(transcript_path)
    if not cwd:
        sys.exit(0)
    cwd = hw.find_project_root(cwd)

    session_dir = Path(cwd) / ".claude" / "sessions" / session_id
    index_data = hw.read_index(session_dir) or hw.create_index(session_dir, session_id, cwd)

    # ── Stage 2: time/size checkpoint ──
    delta = hw.extract_delta(messages, index_data.get("last_processed_uuid") or "")
    if not delta:
        if messages:
            index_data["last_processed_uuid"] = messages[-1].get("uuid", "")
            hw._write_index_file(session_dir, index_data,
                                 hw.parse_frontmatter((session_dir / "INDEX.md").read_text())[1])
        sys.exit(0)
    delta_text, was_truncated = hw.truncate_messages(delta)
    if not should_checkpoint(index_data, delta_text):
        sys.exit(0)
    # Race condition guard: re-read index to catch processes that read the same
    # stale timestamp. Reduces but does not eliminate duplicate writes — a full
    # fix would require file locking or atomic rename (out of scope here).
    fresh = hw.read_index(session_dir)
    if fresh and fresh.get("last_context_written_at") != index_data.get("last_context_written_at"):
        sys.exit(0)
    result = hw.call_claude_narration(delta_text, was_truncated)
    if not result:
        sys.exit(0)
    commits = hw.get_git_commits(cwd, index_data.get("context_head"), index_data.get("started"))
    title = result.get("title", "untitled")
    narration = result.get("narration", "")
    one_liner = narration.split("。")[0].split(".")[0][:80] if narration else title
    num = hw.get_next_context_number(session_dir)
    hw.write_context_file(session_dir, num, title, narration, commits, session_id)
    new_head = hw.get_git_head(cwd)
    last_uuid = delta[-1].get("uuid", "")
    hw.update_index(session_dir, index_data, last_uuid, new_head, num, title, one_liner)


if __name__ == "__main__":
    main()
