import json
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
    assert dd.parse_transcript("/nonexistent/path.jsonl") == []


def test_detect_domains_free_form_returns_list():
    messages = [{"role": "user", "text": "kubernetes pod를 배포하고 싶어"}]
    llm_result = json.dumps(["kubernetes"])
    fake_output = json.dumps({"result": llm_result})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    with mock.patch("subprocess.run", return_value=fake_proc):
        result = dd.detect_domains_free_form(messages)
    assert result == ["kubernetes"]


def test_detect_domains_free_form_empty_messages():
    assert dd.detect_domains_free_form([]) == []


def test_detect_domains_free_form_subprocess_failure():
    messages = [{"role": "user", "text": "some text"}]
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 1
    with mock.patch("subprocess.run", return_value=fake_proc):
        assert dd.detect_domains_free_form(messages) == []


def test_detect_domains_free_form_invalid_json_result():
    messages = [{"role": "user", "text": "some text"}]
    fake_output = json.dumps({"result": "not valid json"})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    with mock.patch("subprocess.run", return_value=fake_proc):
        assert dd.detect_domains_free_form(messages) == []


def test_detect_domains_free_form_truncates_window():
    # 25 messages supplied; only the last 20 should appear in the prompt
    messages = [{"role": "user", "text": f"msg {i}"} for i in range(25)]
    fake_output = json.dumps({"result": "[]"})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    with mock.patch("subprocess.run", return_value=fake_proc) as m:
        dd.detect_domains_free_form(messages)
    prompt_sent = m.call_args.kwargs.get("input", m.call_args[1].get("input", ""))
    assert "msg 4" not in prompt_sent   # first 5 messages dropped
    assert "msg 24" in prompt_sent      # last message included
