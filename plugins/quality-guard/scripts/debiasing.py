import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from feedback_io import load_feedback_rules


_CORE_DEBIASING_CONTEXT = """\
<cognitive-debiasing>
Before responding, execute in order:
1. SUSPEND: Bracket any prior assumptions influencing this response.
2. ENUMERATE: List ALL available options before filtering any out.
3. MULTI-AXIS: Identify 2+ solution axes (not just "how" — also "when", "who", "what triggers").
4. VERIFY: Do your options cover the full option space?
5. COUNTER: Assume your leading approach is wrong. State at least one reason why.
   Adjust or explicitly confirm after examining the objection.
6. EVALUATE: Select using ONLY correctness, standard compliance, and maintainability.
   Prohibited criteria: fewer changes / faster / more familiar / lower risk to you.
7. DECLARE: Root cause in one sentence. Confirm this is structural, not symptomatic.
</cognitive-debiasing>"""


def build_core_debiasing() -> str:
    return _CORE_DEBIASING_CONTEXT


def assemble_context(parts: list[str]) -> str:
    non_empty = [p for p in parts if p]
    return "\n\n---\n\n".join(non_empty)


def _load_pending_review_count(cwd: str) -> int:
    path = Path(cwd) / ".claude" / "quality" / "pending_review.txt"
    if not path.exists():
        return 0
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd", "") or os.getcwd()
    context_parts = [build_core_debiasing()]
    rules = load_feedback_rules(cwd)
    if rules:
        context_parts.append(f"<feedback-rules>\n{rules}\n</feedback-rules>")
    pending = _load_pending_review_count(cwd)
    if pending > 0:
        context_parts.append(
            f"<quality-guard-notice>\n"
            f"{pending} auto-detected quality issue(s) are pending review. "
            f"Run /quality-guard:triage to inspect and approve or reject them.\n"
            f"</quality-guard-notice>"
        )
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
