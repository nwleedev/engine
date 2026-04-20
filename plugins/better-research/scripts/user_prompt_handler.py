import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from inject_research import (
    assemble_context,
    build_anti_frame_bias_context,
    build_perspective_context,
    detect_design_keyword,
    load_skill_md,
)

_MARKER_RE = re.compile(r'(?<![a-zA-Z0-9_/])/(q|query|research)(?=\s|[^\w/]|$)', re.IGNORECASE)
_WS_RE = re.compile(r' {2,}')


def detect_marker(prompt: str) -> bool:
    return bool(_MARKER_RE.search(prompt))


def strip_marker(prompt: str) -> str:
    result = _MARKER_RE.sub(" ", prompt)
    return _WS_RE.sub(" ", result).strip()


def extract_perspectives() -> str:
    return os.environ.get("RESEARCH_PERSPECTIVES", "").strip()


def main_with_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        return
    prompt = payload.get("prompt", "")
    if not prompt:
        return

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    context_parts = []

    # D path: inject active research perspectives from env
    perspectives = extract_perspectives()
    if perspectives:
        context_parts.append(build_perspective_context(perspectives))

    # Layer 1b: inject anti-frame-bias when design/brainstorming keywords detected
    if detect_design_keyword(prompt):
        context_parts.append(build_anti_frame_bias_context())

    # Layer 2 / C path: inject SKILL.md when research marker detected
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
