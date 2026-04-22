import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from inject_research import (
    assemble_context,
    build_perspective_context,
    load_skill_md,
)
from feedback_io import load_raw_since_checkpoint

_MARKER_RE = re.compile(r'(?<![a-zA-Z0-9_/])/(q|query|research)(?=\s|[^\w/]|$)', re.IGNORECASE)
_WS_RE = re.compile(r' {2,}')


def detect_marker(prompt: str) -> bool:
    return bool(_MARKER_RE.search(prompt))


def strip_marker(prompt: str) -> str:
    result = _MARKER_RE.sub(" ", prompt)
    return _WS_RE.sub(" ", result).strip()


def extract_perspectives() -> str:
    return os.environ.get("RESEARCH_PERSPECTIVES", "").strip()


def build_raw_feedback_context(entries: list[str]) -> str:
    lines = "\n".join(f'- "{e}"' for e in entries)
    return f"<session-feedback-observations>\n이 세션에서 관찰된 편향 패턴 (사용자가 직접 기록):\n{lines}\n</session-feedback-observations>"


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    prompt = payload.get("prompt", "")
    if not prompt:
        return
    cwd = payload.get("cwd", "") or os.getcwd()
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    context_parts = []

    perspectives = extract_perspectives()
    if perspectives:
        context_parts.append(build_perspective_context(perspectives))

    raw_entries = load_raw_since_checkpoint(cwd)
    if raw_entries:
        context_parts.append(build_raw_feedback_context(raw_entries))

    if detect_marker(prompt):
        cleaned = strip_marker(prompt)
        if cleaned:
            skill_content = load_skill_md(plugin_root)
            if skill_content:
                context_parts.append(skill_content)

    if not context_parts:
        return

    context = assemble_context(context_parts)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
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
