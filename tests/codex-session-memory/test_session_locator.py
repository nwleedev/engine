from pathlib import Path
import pytest
import session_locator as sl


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)


FAKE_THREAD = "00000000-0000-0000-0000-000000000001"
OTHER_THREAD = "00000000-0000-0000-0000-000000000002"


def test_thread_id_from_env(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", FAKE_THREAD)
    assert sl.current_thread_id() == FAKE_THREAD


def test_thread_id_returns_none_when_unset():
    assert sl.current_thread_id() is None


def test_find_jsonl_for_thread(tmp_path):
    sessions = tmp_path / "sessions" / "2026" / "05" / "01"
    sessions.mkdir(parents=True)
    target = sessions / f"rollout-2026-05-01T00-00-00-{FAKE_THREAD}.jsonl"
    target.write_text("")
    other = sessions / f"rollout-2026-05-01T00-00-01-{OTHER_THREAD}.jsonl"
    other.write_text("")
    found = sl.find_jsonl_by_thread(FAKE_THREAD, codex_sessions_root=str(tmp_path / "sessions"))
    assert found == target.resolve()


def test_find_jsonl_returns_none_when_missing(tmp_path):
    (tmp_path / "sessions").mkdir()
    assert sl.find_jsonl_by_thread("nonexistent-thread-id", codex_sessions_root=str(tmp_path / "sessions")) is None


def test_data_session_dir_under_root(tmp_path):
    fake = "00000000-0000-0000-0000-000000000abc"
    p = sl.data_session_dir(str(tmp_path), fake)
    assert p == (tmp_path / ".codex" / "sessions" / fake).resolve()
