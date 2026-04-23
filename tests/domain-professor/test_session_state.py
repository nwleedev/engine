import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import session_state as ss


def test_get_flag_path_uses_session_id(tmp_path):
    payload = {"session_id": "abc123", "cwd": str(tmp_path)}
    result = ss.get_flag_path(payload, str(tmp_path))
    assert result == tmp_path / ".claude" / "sessions" / "abc123" / ".professor-active"


def test_get_flag_path_fallback_transcript(tmp_path):
    payload = {
        "transcript_path": str(tmp_path / ".claude" / "sessions" / "abc123" / "transcript.jsonl")
    }
    result = ss.get_flag_path(payload, str(tmp_path))
    assert result == tmp_path / ".claude" / "sessions" / "abc123" / ".professor-active"


def test_get_flag_path_returns_none_when_no_session(tmp_path):
    assert ss.get_flag_path({}, str(tmp_path)) is None


def test_is_active_false_when_flag_missing(tmp_path):
    assert ss.is_active(tmp_path / ".professor-active") is False


def test_is_active_true_when_flag_exists(tmp_path):
    flag = tmp_path / ".professor-active"
    flag.touch()
    assert ss.is_active(flag) is True


def test_is_active_false_for_none():
    assert ss.is_active(None) is False


def test_activate_creates_flag_and_parents(tmp_path):
    flag = tmp_path / "sessions" / "abc" / ".professor-active"
    ss.activate(flag)
    assert flag.exists()


def test_deactivate_removes_flag(tmp_path):
    flag = tmp_path / ".professor-active"
    flag.touch()
    ss.deactivate(flag)
    assert not flag.exists()


def test_deactivate_is_safe_when_missing(tmp_path):
    ss.deactivate(tmp_path / ".professor-active")  # must not raise


def test_read_skill_content_returns_text(tmp_path):
    fake = tmp_path / "SKILL.md"
    fake.write_text("# Domain Professor\n", encoding="utf-8")
    with mock.patch.object(ss, "_SKILL_MD_PATH", fake):
        assert "Domain Professor" in ss.read_skill_content()


def test_read_skill_content_empty_on_missing():
    with mock.patch.object(ss, "_SKILL_MD_PATH", Path("/no/such/SKILL.md")):
        assert ss.read_skill_content() == ""


def test_get_textbooks_dir(tmp_path):
    result = ss.get_textbooks_dir(str(tmp_path))
    assert result == tmp_path / ".claude" / "textbooks"
