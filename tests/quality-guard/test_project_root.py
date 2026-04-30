import sys
import subprocess
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import project_root as pr


def _init_git_repo(path: Path):
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)


def test_env_var_wins(tmp_path, monkeypatch):
    repo = tmp_path / "monorepo"
    sub = repo / "web"
    sub.mkdir(parents=True)
    _init_git_repo(sub)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    assert Path(pr.find_project_root(str(sub))) == repo


def test_env_var_ignored_when_path_missing(tmp_path, monkeypatch):
    repo = tmp_path / "monorepo"
    repo.mkdir()
    _init_git_repo(repo)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "missing"))
    assert Path(pr.find_project_root(str(repo))) == repo


def test_topmost_claude_when_no_env(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (outer / ".claude").mkdir()
    (inner / ".claude").mkdir()
    assert Path(pr.find_project_root(str(inner))) == outer


def test_git_toplevel_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    repo = tmp_path / "r"
    repo.mkdir()
    _init_git_repo(repo)
    sub = repo / "pkg"
    sub.mkdir()
    assert Path(pr.find_project_root(str(sub))) == repo


def test_cwd_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    p = tmp_path / "loose"
    p.mkdir()
    assert Path(pr.find_project_root(str(p))) == p
