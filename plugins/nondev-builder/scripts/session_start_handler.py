import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from nondev_io import read_index


def build_context(cwd: str) -> str:
    index = read_index(cwd)
    if not index:
        return (
            "No nondev domain configured. "
            "Run /nondev-setup to set up a professional domain environment."
        )
    domains = index.get("domains", [])
    if not domains:
        return (
            "No nondev domain configured. "
            "Run /nondev-setup to set up a professional domain environment."
        )
    names = [d["task_name"] for d in domains]
    command_list = ", ".join(f"/{n}" for n in names)
    return (
        f"Configured nondev domains: {', '.join(names)}\n"
        f"Run {command_list} [goal] to start a professional workflow."
    )


def main_with_payload(payload: object) -> None:
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
