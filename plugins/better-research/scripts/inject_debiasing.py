import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from inject_research import build_anti_frame_bias_context


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    context = build_anti_frame_bias_context()
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
