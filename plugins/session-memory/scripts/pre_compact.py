#!/usr/bin/env python3
"""PreCompact hook: writes CONTEXT file before compaction."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import handwrite_context as hw


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")
    if not transcript_path or not session_id:
        sys.exit(0)

    try:
        cwd, messages = hw.parse_transcript(transcript_path)
        if not cwd:
            sys.exit(0)
        cwd = hw.find_project_root(cwd)
        session_dir = Path(cwd) / ".claude" / "sessions" / session_id
        index_data = hw.read_index(session_dir) or hw.create_index(session_dir, session_id, cwd)

        # Write CONTEXT file capturing work done since last checkpoint
        delta = hw.extract_delta(messages, index_data.get("last_processed_uuid") or "")
        if delta:
            delta_text, was_truncated = hw.truncate_messages(delta)
            try:
                result = hw.call_claude_narration(delta_text, was_truncated)
                if result:
                    commits = hw.get_git_commits(
                        cwd, index_data.get("context_head"), index_data.get("started")
                    )
                    title = result.get("title") or "checkpoint-" + datetime.utcnow().strftime("%m%d-%H%M")
                    narration = result.get("narration", "")
                    one_liner = narration.split("。")[0].split(".")[0][:80] if narration else title
                    num = hw.get_next_context_number(session_dir)
                    hw.write_context_file(session_dir, num, title, narration, commits, session_id)
                    new_head = hw.get_git_head(cwd)
                    last_uuid = delta[-1].get("uuid", "")
                    hw.update_index(session_dir, index_data, last_uuid, new_head, num, title, one_liner)
            except Exception as e:
                print(f"[pre_compact] narration failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[pre_compact] error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
