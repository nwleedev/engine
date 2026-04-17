#!/usr/bin/env python3
"""PreCompact hook: writes CONTEXT before compaction and injects INDEX.md into compaction prompt."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import handwrite_context as hw


def build_custom_instructions(index_content):
    """Format INDEX.md content into custom instructions for the compaction summary prompt.

    Returns empty string when index_content is empty — caller should skip stdout output.
    """
    if not index_content:
        return ""
    return (
        "When summarizing this conversation, you MUST preserve the following\n"
        "session context recorded in INDEX.md. Include it verbatim at the\n"
        'end of your summary under a "## Session Index" heading.\n\n'
        "--- INDEX.md ---\n"
        f"{index_content}\n"
        "--- END INDEX.md ---"
    )


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

        # Output INDEX.md content as custom instructions for the compaction prompt
        index_path = session_dir / "INDEX.md"
        if index_path.exists():
            index_content = index_path.read_text(encoding="utf-8")
            instructions = build_custom_instructions(index_content)
            if instructions:
                print(instructions)
    except Exception as e:
        print(f"[pre_compact] error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
