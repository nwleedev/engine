from __future__ import annotations

import subprocess
from pathlib import Path

from research_prompt.scanner import (
    collect_dependency_candidates,
    collect_git_context,
    collect_git_diff_candidates,
    collect_symbol_candidates,
)


def _git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def test_collect_git_context_records_status_and_diff(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test User")
    (project / "app.py").write_text("print('old')\n", encoding="utf-8")
    _git(project, "add", "app.py")
    _git(project, "commit", "-m", "initial")
    (project / "app.py").write_text("print('new')\n", encoding="utf-8")

    context, warnings = collect_git_context(project)

    assert warnings == []
    assert any("Git status:" in item for item in context)
    assert any("app.py" in item for item in context)


def test_collect_git_diff_candidates_marks_changed_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test User")
    (project / "app.py").write_text("print('old')\n", encoding="utf-8")
    _git(project, "add", "app.py")
    _git(project, "commit", "-m", "initial")
    (project / "app.py").write_text("print('new')\n", encoding="utf-8")

    candidates, warnings = collect_git_diff_candidates(project)

    assert warnings == []
    assert candidates[0].path == Path("app.py")
    assert candidates[0].signals == {"git_diff": 1}


def test_collect_symbol_candidates_uses_rg_style_text_search(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")
    (project / "other.py").write_text("def render():\n    return None\n", encoding="utf-8")

    candidates, warnings = collect_symbol_candidates(project, ["login_user"], timeout_seconds=2)

    assert isinstance(warnings, list)
    assert candidates[0].path == Path("auth.py")
    assert candidates[0].signals == {"symbol": 1}


def test_collect_dependency_candidates_finds_config_and_lock_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"dependencies":{"next":"latest"}}\n', encoding="utf-8")
    (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (project / "Dockerfile").write_text("FROM python:3.13\n", encoding="utf-8")
    (project / ".github").mkdir()
    (project / ".github" / "workflows").mkdir()
    (project / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    candidates = collect_dependency_candidates(project)
    paths = {candidate.path.as_posix() for candidate in candidates}

    assert {"package.json", "pnpm-lock.yaml", "Dockerfile", ".github/workflows/ci.yml"} <= paths
