import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import detect_domain as dd


def test_extract_text_string():
    assert dd.extract_text("hello world") == "hello world"


def test_extract_text_list():
    content = [{"type": "text", "text": "hello"}, {"type": "tool_use", "id": "t1"}]
    assert dd.extract_text(content) == "hello"


def test_extract_text_empty_list():
    assert dd.extract_text([]) == ""


def test_parse_transcript_extracts_messages():
    transcript = FIXTURES_DIR / "sample_transcript.jsonl"
    messages = dd.parse_transcript(str(transcript))
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert "kubernetes" in messages[0]["text"].lower()


def test_parse_transcript_missing_file():
    messages = dd.parse_transcript("/nonexistent/path.jsonl")
    assert messages == []


def test_detect_domains_kubernetes():
    messages = [
        {"text": "kubernetes pod를 배포하고 싶어"},
        {"text": "kubectl apply로 deployment를 만들었어"},
        {"text": "namespace 설정이 필요해"},
    ]
    domains = dd.detect_domains(messages, threshold=3)
    assert "kubernetes" in domains


def test_detect_domains_below_threshold():
    messages = [{"text": "kubernetes pod 하나"}]
    domains = dd.detect_domains(messages, threshold=3)
    assert "kubernetes" not in domains


def test_detect_domains_multiple():
    messages = [
        {"text": "docker container를 kubernetes pod로 배포"},
        {"text": "kubectl로 docker image를 실행하는 deployment"},
        {"text": "docker registry에서 kubernetes namespace로"},
    ]
    domains = dd.detect_domains(messages, threshold=3)
    assert "kubernetes" in domains
    assert "docker" in domains


def test_detect_domains_from_transcript():
    transcript = str(FIXTURES_DIR / "sample_transcript.jsonl")
    domains = dd.detect_domains_from_transcript(transcript, threshold=3)
    assert "kubernetes" in domains


def test_detect_domains_empty_messages():
    assert dd.detect_domains([], threshold=3) == []
