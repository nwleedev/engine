import importlib.util
import os
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"


def load_session_locator():
    spec = importlib.util.spec_from_file_location("session_locator", SCRIPTS / "session_locator.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_find_jsonl_by_thread_returns_newest_match(tmp_path):
    locator = load_session_locator()
    old_dir = tmp_path / "2026" / "05" / "02"
    new_dir = tmp_path / "2026" / "05" / "03"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    old_file = old_dir / "rollout-old-thread-123.jsonl"
    new_file = new_dir / "rollout-new-thread-123.jsonl"
    old_file.write_text("old\n", encoding="utf-8")
    new_file.write_text("new\n", encoding="utf-8")
    os.utime(old_file, (100, 100))
    os.utime(new_file, (200, 200))

    assert locator.find_jsonl_by_thread("thread-123", codex_sessions_root=tmp_path) == new_file.resolve()


def test_data_session_dir_supports_hidden_child_sessions(tmp_path):
    locator = load_session_locator()

    assert locator.data_session_dir(str(tmp_path), "main-thread") == (
        tmp_path / ".codex" / "sessions" / "main-thread"
    ).resolve()
    assert locator.data_session_dir(str(tmp_path), "child-thread", role="child") == (
        tmp_path / ".codex" / "sessions" / "_children" / "child-thread"
    ).resolve()
