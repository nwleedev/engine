#!/usr/bin/env python3
"""UserPromptSubmit hook: re-inject context after compaction via flag file."""
import json
import os
import sys
from pathlib import Path

import handwrite_context as hw


def resolve_cwd(payload: dict) -> str:
    return (
        payload.get("cwd", "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.environ.get("PWD", "")
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)

    session_id = payload.get("session_id", "")
    cwd = resolve_cwd(payload)
    if not session_id or not cwd:
        sys.exit(0)

    cwd = hw.find_project_root(cwd)
    sessions_dir = Path(cwd) / ".claude" / "sessions"
    flag_path = sessions_dir / f"compacted.{session_id}.flag"

    if not flag_path.exists():
        sys.exit(0)

    session_dir = sessions_dir / session_id
    try:
        flag_path.unlink(missing_ok=True)
    except Exception:
        pass

    recent = hw.load_recent_context_entries(session_dir)
    if not recent:
        sys.exit(0)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"<session-context>\n{recent}\n</session-context>",
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
