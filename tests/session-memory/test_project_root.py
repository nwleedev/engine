import os
import subprocess
from pathlib import Path
import pytest
import project_root as pr


def _init_git_repo(path: Path):
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)


def test_returns_git_toplevel_when_in_subdir(tmp_path):
    repo = tmp_path / "monorepo"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "packages" / "web"
    sub.mkdir(parents=True)
    assert Path(pr.find_project_root(str(sub))) == repo


def test_returns_topmost_claude_when_no_git(tmp_path):
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (outer / ".claude").mkdir()
    (inner / ".claude").mkdir()
    # Should pick OUTER (topmost), not INNER
    assert Path(pr.find_project_root(str(inner))) == outer


def test_falls_back_to_cwd_when_no_git_no_claude(tmp_path):
    p = tmp_path / "loose"
    p.mkdir()
    assert Path(pr.find_project_root(str(p))) == p


def test_assert_root_canonical_passes_at_git_top(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _init_git_repo(repo)
    pr.assert_root_is_canonical(repo, repo)


def test_assert_root_canonical_raises_at_subdir(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "pkg"
    sub.mkdir()
    with pytest.raises(RuntimeError, match="not git toplevel"):
        pr.assert_root_is_canonical(sub, sub)


def test_detect_subpackage_pollution(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _init_git_repo(repo)
    polluted = repo / "pkg" / ".claude" / "sessions"
    polluted.mkdir(parents=True)
    found = pr.detect_subpackage_pollution(repo)
    assert any(p.name == ".claude" and p.parent.name == "pkg" for p in found)


def test_claude_project_dir_env_takes_priority(tmp_path, monkeypatch):
    repo = tmp_path / "monorepo"
    sub = repo / "web"
    sub.mkdir(parents=True)
    _init_git_repo(sub)  # nested git inside sub; without env, git toplevel = sub
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    assert Path(pr.find_project_root(str(sub))) == repo


def test_claude_project_dir_ignored_when_path_missing(tmp_path, monkeypatch):
    repo = tmp_path / "monorepo"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "web"
    sub.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "does-not-exist"))
    assert Path(pr.find_project_root(str(sub))) == repo


def test_topmost_claude_beats_git_toplevel(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    repo = tmp_path / "monorepo"
    repo.mkdir()
    (repo / ".claude").mkdir()
    sub = repo / "web"
    sub.mkdir()
    _init_git_repo(sub)  # nested git in web
    # Topmost .claude is at monorepo, but git toplevel from web/ is web/.
    # New priority: .claude ancestor wins over git toplevel.
    assert Path(pr.find_project_root(str(sub))) == repo


def test_assert_root_canonical_skips_when_env_set(tmp_path, monkeypatch):
    repo = tmp_path / "monorepo"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "web"
    sub.mkdir()
    _init_git_repo(sub)  # nested git so toplevel from sub = sub, not repo
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    # resolved root = repo (via env), but git toplevel from sub = sub.
    # Without relaxation this would raise; with relaxation it must pass.
    pr.assert_root_is_canonical(repo, sub)


def test_assert_root_canonical_still_enforced_without_env(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    repo = tmp_path / "r"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "pkg"
    sub.mkdir()
    with pytest.raises(RuntimeError, match="not git toplevel"):
        pr.assert_root_is_canonical(sub, sub)
