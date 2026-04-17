import json, os, sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import inject_context as ic
import handwrite_context as hw

def test_resolve_cwd_from_payload():
    assert ic.resolve_cwd({"cwd": "/a/b"}) == "/a/b"

def test_resolve_cwd_from_env():
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/env/proj"}, clear=False):
        assert ic.resolve_cwd({}) == "/env/proj"

def test_resolve_cwd_fallback_pwd():
    env = {"PWD": "/pwd/proj"}
    # Remove CLAUDE_PROJECT_DIR if present
    env_without = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env_without.update(env)
    with mock.patch.dict(os.environ, env_without, clear=True):
        assert ic.resolve_cwd({}) == "/pwd/proj"

def test_resolve_cwd_returns_empty_when_all_fail():
    with mock.patch.dict(os.environ, {}, clear=True):
        assert ic.resolve_cwd({}) == ""

def test_inject_context_delegates_find_project_root(tmp_path):
    """inject_context.main() calls hw.find_project_root, not its own copy."""
    # Confirm the attribute comes from handwrite_context, not inject_context
    assert not hasattr(ic, "find_project_root"), (
        "inject_context must not define find_project_root — it should delegate to hw"
    )
    # Canonical coverage of find_project_root logic lives in test_handwrite.py
    assert callable(hw.find_project_root)

def test_load_recent_sessions_excludes_current(tmp_path):
    sessions_dir = tmp_path / ".claude" / "sessions"
    # Create two sessions
    for sid in ["sess-a", "sess-b"]:
        d = sessions_dir / sid
        (d / "contexts").mkdir(parents=True)
        (d / "INDEX.md").write_text(
            f"---\nsession_id: {sid}\nlast_updated: 2026-04-16T10:00:00\n---\n\n# 요약\n"
        )
    sessions = ic.load_recent_sessions(sessions_dir, current_session_id="sess-a")
    ids = [s[2]["session_id"] for s in sessions]
    assert "sess-a" not in ids
    assert "sess-b" in ids

def test_build_context_text_includes_session_id(tmp_path):
    sessions_dir = tmp_path / ".claude" / "sessions"
    sid = "sess-xyz"
    d = sessions_dir / sid
    (d / "contexts").mkdir(parents=True)
    (d / "INDEX.md").write_text(
        f"---\nsession_id: {sid}\nlast_updated: 2026-04-16T10:00:00\n---\n\n# 요약\n작업 진행 중\n"
    )
    sessions = ic.load_recent_sessions(sessions_dir, current_session_id="other")
    text = ic.build_context_text(sessions)
    assert "sess-xyz" in text
    assert "이전 작업 컨텍스트" in text

def test_main_returns_additional_context(tmp_path):
    sessions_dir = tmp_path / ".claude" / "sessions"
    sid = "sess-prev"
    d = sessions_dir / sid
    (d / "contexts").mkdir(parents=True)
    (d / "INDEX.md").write_text(
        f"---\nsession_id: {sid}\nlast_updated: 2026-04-16T10:00:00\n---\n\n# 요약\n이전 작업\n"
    )
    payload = json.dumps({"session_id": "sess-new", "cwd": str(tmp_path)})
    import io
    sys.stdin = io.StringIO(payload)
    captured = io.StringIO()
    try:
        with mock.patch("sys.stdout", captured):
            ic.main()
    except SystemExit:
        pass
    finally:
        sys.stdin = sys.__stdin__
    output = captured.getvalue()
    assert output.strip(), "main() produced no output despite a prior session existing"
    data = json.loads(output)
    assert "additionalContext" in data.get("hookSpecificOutput", {})
