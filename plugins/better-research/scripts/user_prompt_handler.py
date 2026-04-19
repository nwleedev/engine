import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from inject_research import load_skill_md, build_perspective_context, assemble_context

_MARKER_RE = re.compile(r'(?<!\S)/(q|query|research)(?!\S)', re.IGNORECASE)


def detect_marker(prompt: str) -> bool:
    return bool(_MARKER_RE.search(prompt))


def strip_marker(prompt: str) -> str:
    return _MARKER_RE.sub(" ", prompt).strip()


def extract_perspectives() -> str:
    return os.environ.get("RESEARCH_PERSPECTIVES", "").strip()


def main_with_payload(payload: dict) -> None:
    prompt = payload.get("prompt", "")
    if not prompt:
        return

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    context_parts = []

    # D path: inject active research perspectives from env
    perspectives = extract_perspectives()
    if perspectives:
        context_parts.append(build_perspective_context(perspectives))

    # C path: independent of D — inject SKILL.md when marker detected
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
    except (json.JSONDecodeError, EOFError):
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
