import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from inject_research import build_core_debiasing, assemble_context
from feedback_io import load_feedback_rules


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd", "") or os.getcwd()
    context_parts = [build_core_debiasing()]
    rules = load_feedback_rules(cwd)
    if rules:
        context_parts.append(f"<feedback-rules>\n{rules}\n</feedback-rules>")
    context = assemble_context(context_parts)
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
