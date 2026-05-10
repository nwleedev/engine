import importlib.util
from pathlib import Path


def load_project_root():
    path = Path("plugins/codex/quality-guard/scripts/project_root.py").resolve()
    spec = importlib.util.spec_from_file_location("test_cqg_project_root", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys

    sys.modules["test_cqg_project_root"] = module
    spec.loader.exec_module(module)
    return module


def test_env_project_dir_wins(tmp_path, monkeypatch):
    project_root = load_project_root()
    root = tmp_path / "root"
    child = root / "child"
    child.mkdir(parents=True)
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(root))
    assert project_root.find_project_root(str(child)) == str(root.resolve())


def test_agents_md_ancestor_used_without_git(tmp_path, monkeypatch):
    project_root = load_project_root()
    root = tmp_path / "root"
    child = root / "child" / "leaf"
    child.mkdir(parents=True)
    (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
    monkeypatch.delenv("CODEX_PROJECT_DIR", raising=False)
    monkeypatch.setattr(project_root, "_git_toplevel", lambda cwd: "")
    assert project_root.find_project_root(str(child)) == str(root.resolve())


def test_cwd_used_when_no_marker(tmp_path, monkeypatch):
    project_root = load_project_root()
    cwd = tmp_path / "plain"
    cwd.mkdir()
    monkeypatch.delenv("CODEX_PROJECT_DIR", raising=False)
    monkeypatch.setattr(project_root, "_git_toplevel", lambda cwd: "")
    assert project_root.find_project_root(str(cwd)) == str(cwd.resolve())
