import os
from pathlib import Path

import pytest

import bind


def test_render_contains_target_path(tmp_path):
    out = bind._render(tmp_path)
    assert str(tmp_path) in out
    assert str(tmp_path / ".claude" / "settings.local.json") in out
    assert "CLAUDE_PROJECT_DIR" in out
    assert "pbcopy" in out


def test_resolve_with_explicit_path(tmp_path):
    target = tmp_path / "myproj"
    target.mkdir()
    assert bind._resolve_target(str(target), str(tmp_path)) == target.resolve()


def test_resolve_rejects_missing_path(tmp_path):
    with pytest.raises(SystemExit):
        bind._resolve_target(str(tmp_path / "missing"), str(tmp_path))


def test_resolve_auto_ignores_env(tmp_path, monkeypatch):
    """Auto-detect must NOT echo a stale CPD; it should re-resolve from cwd."""
    project = tmp_path / "real_project"
    (project / ".claude").mkdir(parents=True)
    sub = project / "sub"
    sub.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "wrong"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = bind._resolve_target(None, str(sub))
    assert result == project.resolve()
    # env preserved
    assert os.environ.get("CLAUDE_PROJECT_DIR") == str(tmp_path / "wrong")
