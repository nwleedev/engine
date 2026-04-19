import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import find_project_root, resolve_cwd, get_harness_dir
from detect_domain import load_harness_files, detect_domain_from_file_path
from inject_harness import build_pre_tool_context


def main_with_payload(payload: dict) -> None:
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    cwd = resolve_cwd(payload)
    if not cwd:
        return

    project_root = find_project_root(cwd)
    harness_dir = get_harness_dir(project_root)
    harness_files = load_harness_files(harness_dir)
    if not harness_files:
        return

    matched = detect_domain_from_file_path(file_path, harness_files)
    if not matched:
        return

    context = build_pre_tool_context(matched)
    if not context:
        return

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
