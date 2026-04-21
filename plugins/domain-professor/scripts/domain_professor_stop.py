import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from detect_domain import detect_domains_from_transcript
from generate_textbook import find_project_root, generate_for_domains


def main_with_payload(payload: dict) -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return
    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return
    cwd = (
        payload.get("cwd", "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.environ.get("PWD", "")
    )
    if not cwd:
        return
    domains = detect_domains_from_transcript(transcript_path)
    if not domains:
        return
    project_root = find_project_root(cwd)
    generate_for_domains(domains, project_root)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
