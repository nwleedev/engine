#!/usr/bin/env python3
"""PreCompact hook: writes context file before compaction."""
import json
import os
import sys
from pathlib import Path

import handwrite_context as hw
import lang_detect


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

    lang = lang_detect.detect(cwd)

    session_dir = Path(cwd) / ".claude" / "sessions" / session_id
    index_data = hw.read_index(session_dir) or hw.create_index(session_dir, session_id, cwd)

    delta = hw.extract_delta(messages, index_data.get("last_processed_uuid") or "")
    if delta:
        delta_text, was_truncated = hw.truncate_messages(delta)
        try:
            result = hw.call_claude_narration(delta_text, was_truncated, lang)
            if result:
                title = result.get("title") or "checkpoint-" + hw._utcnow().strftime("%m%d-%H%M")
                what_why = result.get("what_why", "")
                one_liner = what_why.split("。")[0].split(".")[0][:80] if what_why else title
                filename = hw.write_context_file(str(session_dir), title, lang, result, session_id)
                new_head = hw.get_git_head(cwd)
                last_uuid = delta[-1].get("uuid", "")
                hw.update_index(session_dir, index_data, last_uuid, new_head, filename, one_liner)
        except Exception as e:
            print(f"[pre_compact] error: {e}", file=sys.stderr)

    flag_path = Path(cwd) / ".claude" / "sessions" / f"compacted.{session_id}.flag"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        flag_path.write_text(session_id, encoding="utf-8")
    except Exception:
        pass

    recent = hw.load_recent_context_entries(session_dir)
    if recent:
        output = {"systemMessage": f"<session-context>\n{recent}\n</session-context>"}
        print(json.dumps(output, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()
