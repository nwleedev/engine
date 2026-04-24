# tests/quality-guard/test_quality_analyzer.py
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import quality_analyzer as qa


# --- extract_qr_pairs ---

def test_extract_qr_pairs_basic():
    lines = [
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "What is X?"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "X is a thing. " * 20}]}}),
    ]
    pairs = qa.extract_qr_pairs("\n".join(lines))
    assert len(pairs) == 1
    assert pairs[0]["question"] == "What is X?"
    assert "X is a thing." in pairs[0]["answer"]


def test_extract_qr_pairs_skips_short_answers():
    lines = [
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Done?"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Yes."}]}}),
    ]
    pairs = qa.extract_qr_pairs("\n".join(lines))
    assert pairs == []


def test_extract_qr_pairs_multiple():
    lines = [
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Q1"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "A" * 250}]}}),
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Q2"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "B" * 250}]}}),
    ]
    pairs = qa.extract_qr_pairs("\n".join(lines))
    assert len(pairs) == 2
    assert pairs[0]["question"] == "Q1"
    assert pairs[1]["question"] == "Q2"


def test_extract_qr_pairs_no_assistant_after_user():
    lines = [
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Hello"}]}}),
    ]
    pairs = qa.extract_qr_pairs("\n".join(lines))
    assert pairs == []


def test_extract_qr_pairs_empty_transcript():
    assert qa.extract_qr_pairs("") == []


def test_extract_qr_pairs_ignores_invalid_json_lines():
    lines = [
        "not json",
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Q"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "A" * 250}]}}),
    ]
    pairs = qa.extract_qr_pairs("\n".join(lines))
    assert len(pairs) == 1


# --- build_analysis_prompt ---

def test_build_analysis_prompt_includes_pairs():
    pairs = [
        {"index": 0, "question": "How do I do X?", "answer": "You should do Y because Z."},
    ]
    prompt = qa.build_analysis_prompt(pairs)
    assert "How do I do X?" in prompt
    assert "You should do Y" in prompt
    assert "3" in prompt  # "at most 3"


def test_build_analysis_prompt_includes_not_vague_exclusions():
    pairs = [{"index": 0, "question": "Q", "answer": "A" * 50}]
    prompt = qa.build_analysis_prompt(pairs)
    assert "yes/no" in prompt.lower() or "NOT vague" in prompt or "not vague" in prompt.lower()


def test_build_analysis_prompt_requests_json_output():
    pairs = [{"index": 0, "question": "Q", "answer": "A"}]
    prompt = qa.build_analysis_prompt(pairs)
    assert "JSON" in prompt or "json" in prompt.lower()
    assert "confidence" in prompt.lower()


# --- parse_analysis_result ---

def test_parse_analysis_result_extracts_high_confidence():
    raw = json.dumps([
        {"index": 0, "reason": "vague claim", "confidence": "high"},
        {"index": 1, "reason": "ok", "confidence": "low"},
    ])
    result = qa.parse_analysis_result(raw)
    assert len(result) == 1
    assert result[0]["index"] == 0
    assert result[0]["confidence"] == "high"


def test_parse_analysis_result_empty_list():
    raw = "[]"
    assert qa.parse_analysis_result(raw) == []


def test_parse_analysis_result_handles_preamble():
    raw = 'Some text before.\n[{"index": 0, "reason": "vague", "confidence": "high"}]'
    result = qa.parse_analysis_result(raw)
    assert len(result) == 1


def test_parse_analysis_result_invalid_json_returns_empty():
    assert qa.parse_analysis_result("not json") == []


def test_parse_analysis_result_filters_non_high_confidence():
    raw = json.dumps([
        {"index": 0, "reason": "r1", "confidence": "medium"},
        {"index": 1, "reason": "r2", "confidence": "high"},
        {"index": 2, "reason": "r3", "confidence": "low"},
    ])
    result = qa.parse_analysis_result(raw)
    assert len(result) == 1
    assert result[0]["index"] == 1


# --- record_detections ---

def test_record_detections_appends_to_raw_md(tmp_path):
    pairs = [
        {"index": 0, "question": "Q1", "answer": "A1"},
    ]
    detections = [{"index": 0, "reason": "vague claim", "confidence": "high"}]
    qa.record_detections(str(tmp_path), pairs, detections)
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    assert raw.exists()
    content = raw.read_text(encoding="utf-8")
    assert "[auto-detected]" in content
    assert "vague claim" in content


def test_record_detections_writes_pending_review_count(tmp_path):
    pairs = [{"index": 0, "question": "Q", "answer": "A"}]
    detections = [{"index": 0, "reason": "vague", "confidence": "high"}]
    qa.record_detections(str(tmp_path), pairs, detections)
    pending = tmp_path / ".claude" / "quality" / "pending_review.txt"
    assert pending.exists()
    assert pending.read_text(encoding="utf-8").strip() == "1"


def test_record_detections_no_detections_does_not_create_pending_file(tmp_path):
    qa.record_detections(str(tmp_path), [], [])
    pending = tmp_path / ".claude" / "quality" / "pending_review.txt"
    assert not pending.exists()


def test_record_detections_multiple_detections_count(tmp_path):
    pairs = [
        {"index": 0, "question": "Q0", "answer": "A0"},
        {"index": 1, "question": "Q1", "answer": "A1"},
    ]
    detections = [
        {"index": 0, "reason": "r0", "confidence": "high"},
        {"index": 1, "reason": "r1", "confidence": "high"},
    ]
    qa.record_detections(str(tmp_path), pairs, detections)
    pending = tmp_path / ".claude" / "quality" / "pending_review.txt"
    assert pending.read_text(encoding="utf-8").strip() == "2"


def test_record_detections_accumulates_across_calls(tmp_path):
    pairs = [{"index": 0, "question": "Q", "answer": "A"}]
    detections = [{"index": 0, "reason": "vague", "confidence": "high"}]
    qa.record_detections(str(tmp_path), pairs, detections)
    qa.record_detections(str(tmp_path), pairs, detections)
    pending = tmp_path / ".claude" / "quality" / "pending_review.txt"
    assert pending.read_text(encoding="utf-8").strip() == "2"


# --- run_quality_analysis (integration with mocked claude -p) ---

def test_run_quality_analysis_full_flow(tmp_path):
    transcript_path = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Explain caching"}]}}),
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "There are several ways to do caching. " * 10}]}}),
    ]
    transcript_path.write_text("\n".join(lines), encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"result": json.dumps([
        {"index": 0, "reason": "vague enumeration", "confidence": "high"}
    ])})
    payload = {"cwd": str(tmp_path), "transcript_path": str(transcript_path)}
    with patch("quality_analyzer.subprocess.run", return_value=mock_result):
        qa.run_quality_analysis(payload, str(tmp_path))
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    assert raw.exists()
    assert "[auto-detected]" in raw.read_text(encoding="utf-8")


def test_run_quality_analysis_skips_when_writing_context(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_WRITING_CONTEXT", "1")
    transcript_path = tmp_path / "transcript.jsonl"
    transcript_path.write_text("", encoding="utf-8")
    with patch("quality_analyzer.subprocess.run") as mock_sub:
        qa.run_quality_analysis({"cwd": str(tmp_path), "transcript_path": str(transcript_path)}, str(tmp_path))
    mock_sub.assert_not_called()


def test_run_quality_analysis_no_transcript_path_is_noop(tmp_path):
    with patch("quality_analyzer.subprocess.run") as mock_sub:
        qa.run_quality_analysis({"cwd": str(tmp_path)}, str(tmp_path))
    mock_sub.assert_not_called()


def test_run_quality_analysis_missing_transcript_file_is_noop(tmp_path):
    with patch("quality_analyzer.subprocess.run") as mock_sub:
        qa.run_quality_analysis(
            {"cwd": str(tmp_path), "transcript_path": str(tmp_path / "nonexistent.jsonl")},
            str(tmp_path),
        )
    mock_sub.assert_not_called()
