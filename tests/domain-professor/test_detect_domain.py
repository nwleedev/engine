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
    messages = dd.parse_transcript("/nonexistent/path.jsonl")
    assert messages == []


def test_get_user_domains_comma_separated():
    with mock.patch.dict("os.environ", {"DOMAIN_PROFESSOR_DOMAINS": "kubernetes,finance,market-research"}):
        domains = dd.get_user_domains()
    assert domains == ["kubernetes", "finance", "market-research"]


def test_get_user_domains_json_array():
    raw = json.dumps(["kubernetes", "docker", "finance"])
    with mock.patch.dict("os.environ", {"DOMAIN_PROFESSOR_DOMAINS": raw}):
        domains = dd.get_user_domains()
    assert domains == ["kubernetes", "docker", "finance"]


def test_get_user_domains_empty():
    with mock.patch.dict("os.environ", {}, clear=True):
        domains = dd.get_user_domains()
    assert domains == []


def test_get_user_domains_strips_whitespace():
    with mock.patch.dict("os.environ", {"DOMAIN_PROFESSOR_DOMAINS": " kubernetes , finance "}):
        domains = dd.get_user_domains()
    assert domains == ["kubernetes", "finance"]


def test_detect_domains_with_llm_returns_filtered_domains():
    messages = [{"role": "user", "text": "kubernetes pod 배포 방법을 알아보자"}]
    domains = ["kubernetes", "finance"]
    llm_result = json.dumps(["kubernetes"])
    fake_output = json.dumps({"result": llm_result})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    with mock.patch("subprocess.run", return_value=fake_proc):
        result = dd.detect_domains_with_llm(messages, domains)
    assert result == ["kubernetes"]


def test_detect_domains_with_llm_filters_invalid_domains():
    messages = [{"role": "user", "text": "some text"}]
    domains = ["kubernetes"]
    # LLM returns a domain not in user's list
    llm_result = json.dumps(["docker"])
    fake_output = json.dumps({"result": llm_result})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    with mock.patch("subprocess.run", return_value=fake_proc):
        result = dd.detect_domains_with_llm(messages, domains)
    assert result == []


def test_detect_domains_with_llm_empty_messages():
    result = dd.detect_domains_with_llm([], ["kubernetes"])
    assert result == []


def test_detect_domains_with_llm_no_domains():
    messages = [{"role": "user", "text": "kubernetes pod"}]
    result = dd.detect_domains_with_llm(messages, [])
    assert result == []


def test_detect_domains_with_llm_subprocess_failure():
    messages = [{"role": "user", "text": "kubernetes pod"}]
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 1
    with mock.patch("subprocess.run", return_value=fake_proc):
        result = dd.detect_domains_with_llm(messages, ["kubernetes"])
    assert result == []


def test_detect_domains_from_transcript_no_env():
    with mock.patch.dict("os.environ", {}, clear=True):
        result = dd.detect_domains_from_transcript("/any/path.jsonl")
    assert result == []


def test_detect_domains_from_transcript_with_env():
    transcript = str(FIXTURES_DIR / "sample_transcript.jsonl")
    llm_result = json.dumps(["kubernetes"])
    fake_output = json.dumps({"result": llm_result})
    fake_proc = mock.MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = fake_output
    env = {"DOMAIN_PROFESSOR_DOMAINS": "kubernetes,finance"}
    with mock.patch.dict("os.environ", env):
        with mock.patch("subprocess.run", return_value=fake_proc):
            result = dd.detect_domains_from_transcript(transcript)
    assert "kubernetes" in result
