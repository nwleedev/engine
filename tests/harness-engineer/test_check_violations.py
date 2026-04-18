import json
import sys
from pathlib import Path
from unittest import mock
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_violations as cv


TRANSCRIPT_PATH = str(FIXTURES_DIR / "sample_transcript.jsonl")
REACT_CONTENT = (FIXTURES_DIR / "sample_harness_react.md").read_text(encoding="utf-8")


# --- extract_claude_code_blocks ---

def test_extract_claude_code_blocks_finds_typescript():
    blocks = cv.extract_claude_code_blocks(TRANSCRIPT_PATH)
    assert len(blocks) >= 1
    assert any("handleClick" in b for b in blocks)


def test_extract_claude_code_blocks_missing_file():
    blocks = cv.extract_claude_code_blocks("/nonexistent/path.jsonl")
    assert blocks == []


def test_extract_claude_code_blocks_str_content(tmp_path):
    jsonl = tmp_path / "transcript.jsonl"
    entry = {
        "uuid": "1",
        "message": {
            "role": "assistant",
            "content": "Here is code:\n```python\nprint('hello')\n```"
        }
    }
    jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    blocks = cv.extract_claude_code_blocks(str(jsonl))
    assert any("print" in b for b in blocks)


# --- parse_violation_line ---

def test_parse_violation_line_valid():
    line = "2026-04-18 | react-frontend | any 타입 사용 | Button.tsx:14 | 3회 반복"
    result = cv.parse_violation_line(line)
    assert result["domain"] == "react-frontend"
    assert result["rule"] == "any 타입 사용"
    assert result["count"] == 3


def test_parse_violation_line_invalid():
    assert cv.parse_violation_line("not a valid line") is None


# --- detect_drift ---

def test_detect_drift_repeated_violation(tmp_path):
    log = tmp_path / "violations.log"
    lines = [
        "2026-04-17 | react-frontend | any 타입 사용 | A.tsx:1 | 2회 반복",
        "2026-04-18 | react-frontend | any 타입 사용 | B.tsx:2 | 3회 반복",
        "2026-04-18 | react-frontend | any 타입 사용 | C.tsx:3 | 1회 반복",
    ]
    log.write_text("\n".join(lines), encoding="utf-8")
    harness_file = tmp_path / "react-frontend.md"
    harness_file.write_text("---\ndomain: react-frontend\n---", encoding="utf-8")
    warnings = cv.detect_drift(log, tmp_path)
    assert any("any 타입 사용" in w for w in warnings)


def test_detect_drift_stale_harness(tmp_path):
    log = tmp_path / "violations.log"
    log.write_text("", encoding="utf-8")
    harness_file = tmp_path / "react-frontend.md"
    harness_file.write_text("---\ndomain: react-frontend\nupdated: 2025-01-01\n---", encoding="utf-8")
    warnings = cv.detect_drift(log, tmp_path)
    assert any("react-frontend" in w and "갱신" in w for w in warnings)


def test_detect_drift_no_issues(tmp_path):
    log = tmp_path / "violations.log"
    log.write_text("", encoding="utf-8")
    warnings = cv.detect_drift(log, tmp_path)
    assert warnings == []


# --- append_violations ---

def test_append_violations_creates_file(tmp_path):
    log_path = tmp_path / "violations.log"
    violations = [
        {"date": "2026-04-18", "domain": "react-frontend",
         "rule": "any 타입 사용", "location": "Button.tsx:14", "count": 1}
    ]
    cv.append_violations(violations, log_path)
    content = log_path.read_text(encoding="utf-8")
    assert "react-frontend" in content
    assert "any 타입 사용" in content


def test_append_violations_appends_to_existing(tmp_path):
    log_path = tmp_path / "violations.log"
    log_path.write_text("existing line\n", encoding="utf-8")
    violations = [
        {"date": "2026-04-18", "domain": "react-frontend",
         "rule": "useEffect 파생 상태", "location": "Form.tsx:32", "count": 1}
    ]
    cv.append_violations(violations, log_path)
    content = log_path.read_text(encoding="utf-8")
    assert "existing line" in content
    assert "useEffect" in content


# --- trim_old_violations ---

def test_trim_old_violations_removes_entries_older_than_90_days(tmp_path):
    log_path = tmp_path / "violations.log"
    log_path.write_text(
        "2020-01-01 | react-frontend | old rule | A.tsx:1 | 1회 반복\n"
        "2026-04-18 | react-frontend | new rule | B.tsx:2 | 1회 반복\n",
        encoding="utf-8"
    )
    cv.trim_old_violations(log_path)
    content = log_path.read_text(encoding="utf-8")
    assert "old rule" not in content
    assert "new rule" in content


def test_trim_old_violations_noop_if_no_file(tmp_path):
    log_path = tmp_path / "violations.log"
    cv.trim_old_violations(log_path)  # must not raise


# --- check_violations_with_llm ---

@mock.patch("subprocess.run")
def test_check_violations_with_llm_sets_writing_context_env(mock_run):
    mock_run.return_value = mock.Mock(returncode=0, stdout='{"result": "[]"}')
    cv.check_violations_with_llm(["some code"], [{"domain": "d", "content": "c"}], "t.jsonl")
    _, kwargs = mock_run.call_args
    assert kwargs["env"]["CLAUDE_WRITING_CONTEXT"] == "1"


@mock.patch("subprocess.run")
def test_check_violations_with_llm_correct_cli_flags(mock_run):
    mock_run.return_value = mock.Mock(returncode=0, stdout='{"result": "[]"}')
    cv.check_violations_with_llm(["code"], [{"domain": "d", "content": "c"}], "t.jsonl")
    cmd = mock_run.call_args[0][0]
    assert cmd == ["claude", "-p", "--no-session-persistence", "--output-format", "json"]


@mock.patch("subprocess.run")
def test_check_violations_with_llm_returns_empty_on_failure(mock_run):
    mock_run.return_value = mock.Mock(returncode=1, stdout="")
    result = cv.check_violations_with_llm(["code"], [{"domain": "d", "content": "c"}], "t.jsonl")
    assert result == []


def test_check_violations_with_llm_returns_empty_for_no_input():
    result = cv.check_violations_with_llm([], [], "t.jsonl")
    assert result == []
