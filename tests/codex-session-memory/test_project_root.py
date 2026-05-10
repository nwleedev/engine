import importlib.util
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"


def load_project_root():
    module_name = "test_codex_session_memory_project_root"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / "project_root.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_find_project_root_prefers_git_toplevel_over_parent_agents(monkeypatch, tmp_path):
    project_root = load_project_root()
    parent = tmp_path / "engine"
    worktree = parent / ".worktrees" / "codex-session-memory-v2"
    child = worktree / "plugins" / "codex" / "session-memory"
    child.mkdir(parents=True)
    (parent / "AGENTS.md").write_text("# parent rules\n", encoding="utf-8")

    monkeypatch.delenv("CODEX_PROJECT_DIR", raising=False)
    monkeypatch.setattr(project_root.Path, "home", lambda: tmp_path.parent)
    monkeypatch.setattr(project_root, "_git_toplevel", lambda cwd: str(worktree))

    assert project_root.find_project_root(str(child)) == str(worktree)
