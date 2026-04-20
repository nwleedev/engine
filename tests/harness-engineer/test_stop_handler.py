import json
import sys
from pathlib import Path
from unittest import mock
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import stop_handler as sh


CODE_HARNESS = {
    "domain": "react-frontend", "domain_type": "code",
    "content": "---\ndomain: react-frontend\n---\n# Body", "keywords": ["tsx"],
    "file_patterns": ["*.tsx"], "language": "auto",
}
DOC_HARNESS = {
    "domain": "market-research", "domain_type": "document",
    "content": "---\ndomain: market-research\n---\n# Body", "keywords": ["market"],
    "file_patterns": [], "language": "auto",
}


# Note: stop_handler uses `from check_violations import X`, so mock targets
# must be `stop_handler.X` (where the name is bound), NOT `check_violations.X`.
# We omit `cwd` from payload so harness_dir resolves to None — keeps tests
# focused on routing logic only, not log-writing side effects.

@mock.patch("stop_handler.check_violations_with_llm", return_value=[])
@mock.patch("stop_handler.extract_claude_code_blocks", return_value=["code"])
def test_code_domain_uses_code_blocks(mock_extract, mock_check):
    payload = {"transcript_path": str(FIXTURES_DIR / "sample_transcript.jsonl")}
    sh.main_with_payload(payload, [CODE_HARNESS])
    mock_extract.assert_called_once()
    mock_check.assert_called_once()


@mock.patch("stop_handler.check_document_violations_with_llm", return_value=[])
@mock.patch("stop_handler.extract_document_sections", return_value=["text section"])
def test_document_domain_uses_document_sections(mock_sections, mock_check):
    payload = {"transcript_path": str(FIXTURES_DIR / "sample_document_transcript.jsonl")}
    sh.main_with_payload(payload, [DOC_HARNESS])
    mock_sections.assert_called_once()
    mock_check.assert_called_once()


@mock.patch("stop_handler.check_violations_with_llm", return_value=[])
@mock.patch("stop_handler.extract_claude_code_blocks", return_value=[])
def test_missing_domain_type_defaults_to_code(mock_extract, mock_check):
    harness_no_type = {k: v for k, v in CODE_HARNESS.items() if k != "domain_type"}
    payload = {"transcript_path": str(FIXTURES_DIR / "sample_transcript.jsonl")}
    sh.main_with_payload(payload, [harness_no_type])
    mock_extract.assert_called_once()


@mock.patch("stop_handler.check_document_violations_with_llm", return_value=[])
@mock.patch("stop_handler.extract_document_sections", return_value=[])
@mock.patch("stop_handler.check_violations_with_llm", return_value=[])
@mock.patch("stop_handler.extract_claude_code_blocks", return_value=["code"])
def test_mixed_domains_routes_both(mock_code_ext, mock_code_check, mock_doc_sections, mock_doc_check):
    payload = {"transcript_path": str(FIXTURES_DIR / "sample_transcript.jsonl")}
    sh.main_with_payload(payload, [CODE_HARNESS, DOC_HARNESS])
    mock_code_ext.assert_called_once()
    mock_doc_sections.assert_called_once()
