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
