import os
import subprocess
from pathlib import Path
import pytest
import project_root as pr


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CODEX_PROJECT_DIR", raising=False)


def test_tier1_env_var_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(tmp_path))
    assert pr.find_project_root(str(tmp_path / "anywhere")) == str(tmp_path.resolve())


def test_tier1_ignored_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_PROJECT_DIR", "/nonexistent/path")
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    (tmp_path / "AGENTS.md").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    assert pr.find_project_root(str(sub)) == str(tmp_path.resolve())


def test_tier3_topmost_agents_md(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    (tmp_path / "AGENTS.md").write_text("root")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "AGENTS.md").write_text("inner")
    assert pr.find_project_root(str(nested)) == str(tmp_path.resolve())


def test_tier4_topmost_codex_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    (tmp_path / ".codex").mkdir()
    sub = tmp_path / "sub"
    sub.mkdir()
    assert pr.find_project_root(str(sub)) == str(tmp_path.resolve())


def test_tier5_git_toplevel(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sub = tmp_path / "a"
    sub.mkdir()
    assert pr.find_project_root(str(sub)) == str(tmp_path.resolve())


def test_tier6_cwd_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    assert pr.find_project_root(str(tmp_path)) == str(tmp_path.resolve())


def test_assert_canonical_passes_when_env_matches(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(tmp_path))
    pr.assert_root_is_canonical(str(tmp_path), str(tmp_path))


def test_assert_canonical_rejects_non_toplevel(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sub = tmp_path / "a"
    sub.mkdir()
    with pytest.raises(RuntimeError, match="not git toplevel"):
        pr.assert_root_is_canonical(str(sub), str(sub))


def test_tier3_ignores_agents_md_when_parent_has_directory_named_AGENTS_md(tmp_path, monkeypatch):
    """A polluted ancestor with a *directory* named AGENTS.md must not capture
    the resolution. Only AGENTS.md as a regular file marks a project root."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path.parent)
    # Polluted ancestor: AGENTS.md as directory
    (tmp_path / "AGENTS.md").mkdir()
    # Real project: AGENTS.md as file at a child level
    project = tmp_path / "real_project"
    project.mkdir()
    (project / "AGENTS.md").write_text("real")
    sub = project / "sub"
    sub.mkdir()
    assert pr.find_project_root(str(sub)) == str(project.resolve())
