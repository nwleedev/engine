import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feedback_io import append_raw_entry, increment_pending_review
from project_root import find_project_root

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

NOT superficial (do not flag these):
- Changing documentation text, placeholder descriptions, or instruction wording
- Using a sentinel value (e.g., epoch timestamp, empty string, zero) as an explicit boundary marker
- Updating a configuration value between two valid options
- Fixing a typo or wording with no behavioral change intended

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

NOT superficial (do not flag these):
- Changing documentation text, placeholder descriptions, or instruction wording
- Using a sentinel value (e.g., epoch timestamp, empty string, zero) as an explicit boundary marker
- Updating a configuration value between two valid options
- Fixing a typo or wording with no behavioral change intended

File: {file_path}
Content:
{content}

Answer exactly:
VERDICT: structural | superficial | unclear
REASON: [one sentence]
CONFIDENCE: high | medium | low"""

def _call_llm(prompt: str) -> str:
    try:
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--model", "claude-haiku-4-5-20251001",
                "--tools", "",
                "--no-session-persistence",
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


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


def _emit_warning(cwd: str, file_path: str, reason: str) -> None:
    print(
        f"[quality-guard] Possible superficial change at {file_path}: {reason}",
        file=sys.stderr,
    )
    entry_text = f"[auto-detected] superficial-edit: {reason} (file: {file_path})"
    try:
        append_raw_entry(cwd, entry_text)
        increment_pending_review(cwd, 1)
    except Exception as exc:
        print(f"[quality-guard] Failed to log warning: {exc}", file=sys.stderr)


def main_with_payload(payload: object, llm_fn: Callable[[str], str] | None = None) -> None:
    if not isinstance(payload, dict):
        return
    if llm_fn is None:
        llm_fn = _call_llm

    cwd_raw = payload.get("cwd") or os.getcwd()
    cwd = find_project_root(cwd_raw)
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
        try:
            verdict, reason, confidence = parse_verdict(llm_fn(prompt))
        except Exception:
            return

    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        if not file_path or not content:
            return
        if not os.path.exists(file_path):
            return
        prompt = _WRITE_PROMPT.format(file_path=file_path, content=content)
        try:
            verdict, reason, confidence = parse_verdict(llm_fn(prompt))
        except Exception:
            return

    else:
        return

    if verdict == "superficial" and confidence == "high":
        _emit_warning(cwd, file_path, reason)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
