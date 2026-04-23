import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from detect_domain import parse_transcript, detect_domains_free_form
from generate_textbook import find_project_root, generate_for_domains
from session_state import get_flag_path, is_active


def resolve_cwd(payload: dict) -> str:
    cwd = payload.get("cwd", "")
    if cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR", os.environ.get("PWD", ""))


def main_with_payload(payload: dict) -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return
    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return
    cwd = resolve_cwd(payload)
    if not cwd:
        return
    project_root = find_project_root(cwd)
    flag = get_flag_path(payload, project_root)
    if not is_active(flag):
        return
    messages = parse_transcript(transcript_path)
    domains = detect_domains_free_form(messages)
    if not domains:
        return
    generate_for_domains(domains, project_root)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
