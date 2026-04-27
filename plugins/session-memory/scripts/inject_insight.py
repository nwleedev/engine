#!/usr/bin/env python3
"""SessionStart hook: injects recent codebase insights as additionalContext."""
import json
import os
import sys

import handwrite_context as hw


def resolve_cwd(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
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

    cwd = resolve_cwd(payload)
    if not cwd:
        sys.exit(0)
    cwd = hw.find_project_root(cwd)

    text = hw.load_recent_insights(cwd)
    if not text:
        sys.exit(0)

    entry_count = len([e for e in text.split("\n---\n") if e.strip()])
    print(f"[session-memory] insight inject: INSIGHT.md ({entry_count} entries)", file=sys.stderr)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"<codebase-insights>\n{text}\n</codebase-insights>",
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
