import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness_io import has_harness_dir, read_all_harness_content


def build_context(cwd: str) -> str:
    if not has_harness_dir(cwd):
        return (
            "No harness found in this project. "
            "Run /harness-setup to configure quality standards for your tech stack."
        )
    harness_dir = str(Path(cwd) / ".claude" / "harness")
    content = read_all_harness_content(harness_dir)
    if not content:
        return (
            "Harness directory exists but contains no domain files. "
            "Run /harness-setup to generate harness standards."
        )
    return f"## Active Harness Standards\n\n{content}"


def main_with_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd") or os.getcwd()
    context = build_context(cwd)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
