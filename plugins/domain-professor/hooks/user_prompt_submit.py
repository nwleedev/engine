#!/usr/bin/env python3
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from inject_toc import find_project_root, resolve_cwd
from session_state import get_flag_path, is_active, read_skill_content


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    cwd = resolve_cwd(payload)
    if not cwd:
        return
    project_root = find_project_root(cwd)
    flag = get_flag_path(payload, project_root)
    if not is_active(flag):
        return
    skill_content = read_skill_content()
    if not skill_content:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": skill_content,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
