from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ref_io import load_index

_REFS_CONTEXT_TEMPLATE = """\
<available-refs>
External reference files are registered for this project.
Before answering, check if any registered ref is relevant to the task.
To read a ref: use the Read tool on the listed path.
To add a ref: use the /add-ref skill.

Registered refs:
{table}
</available-refs>"""


def _cell(value: str) -> str:
    return value.replace("|", "\\|")


def build_refs_context(cwd: str) -> str:
    entries = load_index(cwd)
    if not entries:
        return ""
    lines = ["| Name | Path | Tags |", "|---|---|---|"]
    for e in entries:
        tags = ", ".join(e.get("tags", []))
        lines.append(f"| {_cell(e['name'])} | {_cell(e['path'])} | {_cell(tags)} |")
    return _REFS_CONTEXT_TEMPLATE.format(table="\n".join(lines))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    cwd = (
        payload.get("cwd", "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.getcwd()
    )
    context = build_refs_context(cwd)
    if not context:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
