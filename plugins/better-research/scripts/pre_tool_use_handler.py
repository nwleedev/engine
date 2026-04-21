import json
import os
import sys
from collections.abc import Callable

_EDIT_PROMPT = """\
Evaluate this code change for implementation quality.

SUPERFICIAL changes (mask symptoms without fixing root cause):
- Silencing exceptions without fixing the cause
- Adding bypass flags or conditional routing around broken logic
- Only renaming/reformatting with no behavioral change
- Adding an abstraction layer over broken code
- Hardcoding values that belong in configuration or logic
- Adding special-case branches to work around general logic failures
- Catching exceptions to hide errors instead of fixing them

File: {file_path}
Before:
{old_content}

After:
{new_content}

Answer exactly:
VERDICT: structural | superficial | unclear
REASON: [one sentence]
CONFIDENCE: high | medium | low"""

_WRITE_PROMPT = """\
Evaluate this code for implementation quality.

SUPERFICIAL changes (mask symptoms without fixing root cause):
- Silencing exceptions without fixing the cause
- Adding bypass flags or conditional routing around broken logic
- Only renaming/reformatting with no behavioral change
- Adding an abstraction layer over broken code
- Hardcoding values that belong in configuration or logic
- Adding special-case branches to work around general logic failures
- Catching exceptions to hide errors instead of fixing them

File: {file_path}
Content:
{content}

Answer exactly:
VERDICT: structural | superficial | unclear
REASON: [one sentence]
CONFIDENCE: high | medium | low"""

_BLOCK_MESSAGE = (
    "[better-research] Superficial implementation detected: {reason}\n"
    "Please identify the root cause and implement a structural fix.\n"
    "Use DECLARE (step 6) before calling Edit or Write."
)


def _call_llm(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_verdict(response: str) -> tuple[str, str, str]:
    verdict = "unclear"
    reason = ""
    confidence = "low"
    for line in response.splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip().lower()
        elif line.startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            confidence = line.split(":", 1)[1].strip().lower()
    return verdict, reason, confidence


def should_block(verdict: str, confidence: str) -> bool:
    return verdict == "superficial" and confidence == "high"


def _emit_block(reason: str) -> None:
    output = {
        "decision": "block",
        "reason": _BLOCK_MESSAGE.format(reason=reason),
    }
    print(json.dumps(output, ensure_ascii=False))


def main_with_payload(payload: object, llm_fn: Callable[[str], str] | None = None) -> None:
    if not isinstance(payload, dict):
        return
    if llm_fn is None:
        llm_fn = _call_llm

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return

    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        if not file_path or not old_string or not new_string:
            return
        prompt = _EDIT_PROMPT.format(
            file_path=file_path,
            old_content=old_string,
            new_content=new_string,
        )
        verdict, reason, confidence = parse_verdict(llm_fn(prompt))

    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        if not file_path or not content:
            return
        if not os.path.exists(file_path):
            return
        prompt = _WRITE_PROMPT.format(file_path=file_path, content=content)
        verdict, reason, confidence = parse_verdict(llm_fn(prompt))

    else:
        return

    if should_block(verdict, confidence):
        _emit_block(reason)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
