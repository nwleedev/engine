import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import find_project_root, resolve_cwd, get_harness_dir
from detect_domain import load_harness_files
from check_violations import (
    extract_claude_code_blocks,
    extract_document_sections,
    check_violations_with_llm,
    check_document_violations_with_llm,
    append_violations,
    detect_drift,
    trim_old_violations,
)


def main_with_payload(payload: dict, harness_files: list[dict]) -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path or not harness_files:
        return

    cwd = payload.get("cwd", "")
    project_root = find_project_root(cwd) if cwd else ""
    harness_dir = get_harness_dir(project_root) if project_root else None

    code_harnesses = [f for f in harness_files if f.get("domain_type", "code") == "code"]
    doc_harnesses = [f for f in harness_files if f.get("domain_type", "code") == "document"]

    all_violations: list[dict] = []

    if code_harnesses:
        code_blocks = extract_claude_code_blocks(transcript_path)
        violations = check_violations_with_llm(code_blocks, code_harnesses, transcript_path)
        all_violations.extend(violations)

    if doc_harnesses:
        doc_sections = extract_document_sections(transcript_path)
        violations = check_document_violations_with_llm(doc_sections, doc_harnesses, transcript_path)
        all_violations.extend(violations)

    if harness_dir:
        log_path = harness_dir / "violations.log"
        if all_violations:
            append_violations(all_violations, log_path)
        trim_old_violations(log_path)
        drift_warnings = detect_drift(log_path, harness_dir)
        if drift_warnings:
            summary = "\n".join(f"- {w}" for w in drift_warnings)
            sys.stderr.write(f"[harness-engineer] Drift detected:\n{summary}\n")


def main() -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    cwd = resolve_cwd(payload)
    if not cwd:
        return
    project_root = find_project_root(cwd)
    harness_dir = get_harness_dir(project_root)
    harness_files = load_harness_files(harness_dir)
    if not harness_files:
        return

    main_with_payload(payload, harness_files)


if __name__ == "__main__":
    main()
