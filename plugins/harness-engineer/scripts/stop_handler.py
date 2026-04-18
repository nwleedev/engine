import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import find_project_root, resolve_cwd, get_harness_dir
from detect_domain import load_harness_files
from check_violations import (
    extract_claude_code_blocks,
    check_violations_with_llm,
    append_violations,
    detect_drift,
    trim_old_violations,
)


def main() -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return

    cwd = resolve_cwd(payload)
    if not cwd:
        return

    project_root = find_project_root(cwd)
    harness_dir = get_harness_dir(project_root)
    harness_files = load_harness_files(harness_dir)
    if not harness_files:
        return

    code_blocks = extract_claude_code_blocks(transcript_path)
    violations = check_violations_with_llm(code_blocks, harness_files, transcript_path)

    log_path = harness_dir / "violations.log"
    if violations:
        append_violations(violations, log_path)
    trim_old_violations(log_path)

    drift_warnings = detect_drift(log_path, harness_dir)
    if drift_warnings:
        summary = "\n".join(f"- {w}" for w in drift_warnings)
        sys.stderr.write(f"[harness-engineer] Drift detected:\n{summary}\n")


if __name__ == "__main__":
    main()
