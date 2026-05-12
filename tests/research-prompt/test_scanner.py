from __future__ import annotations

import subprocess
from pathlib import Path

import research_prompt.scanner as scanner
from research_prompt.scanner import (
    collect_code_blocks,
    collect_dependency_candidates,
    collect_git_context,
    collect_git_diff_candidates,
    collect_symbol_candidates,
    merge_candidates,
)
from research_prompt.relevance import CandidateFile


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


def test_merge_candidates_combines_signals_and_preserves_line() -> None:
    candidates = [
        CandidateFile(path=Path("src/app.py"), signals={"user_path": 1}),
        CandidateFile(path=Path("src/app.py"), signals={"stack_trace": 1}, line=7),
        CandidateFile(path=Path("src/app.py"), signals={"symbol": 1}),
    ]

    merged = merge_candidates(candidates)

    assert len(merged) == 1
    assert merged[0].signals == {"user_path": 1, "stack_trace": 1, "symbol": 1}
    assert merged[0].line == 7


def test_collect_code_blocks_records_line_range_and_budget_warnings(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "first.py").write_text("\n".join(f"line {index}" for index in range(1, 20)), encoding="utf-8")
    (project / "second.py").write_text("second = True\n" * 20, encoding="utf-8")

    blocks, warnings = collect_code_blocks(
        project,
        [
            CandidateFile(path=Path("first.py"), signals={"user_path": 1, "stack_trace": 1}, line=5),
            CandidateFile(path=Path("second.py"), signals={"symbol": 1}),
        ],
        max_chars=200,
        max_total_chars=80,
    )

    assert blocks[0]["line_range"] == "1-9"
    assert any("not included due to budget: second.py" in warning for warning in warnings)


def test_collect_code_blocks_denies_outside_and_symlink_targets(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("private notes\n", encoding="utf-8")
    link = project / "linked.txt"
    link.symlink_to(outside)

    blocks, warnings = collect_code_blocks(
        project,
        [
            CandidateFile(path=Path("/etc/hosts"), signals={"stack_trace": 1}),
            CandidateFile(path=Path("../outside.txt"), signals={"stack_trace": 1}),
            CandidateFile(path=Path("linked.txt"), signals={"dependency": 1}),
        ],
    )

    assert blocks == []
    assert any("Denied path outside project: /etc/hosts" in warning for warning in warnings)
    assert any("Denied path outside project: ../outside.txt" in warning for warning in warnings)
    assert any("Denied path outside project: linked.txt" in warning for warning in warnings)


def test_collect_symbol_candidates_falls_back_when_rg_fails(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "auth.py").write_text("def login_user():\n    return True\n", encoding="utf-8")

    def fail_rg(command: list[str], project_root: Path, timeout_seconds: int = 3) -> tuple[str, str | None]:
        return "", "rg failed: not found"

    monkeypatch.setattr(scanner, "_run_read_only", fail_rg)

    candidates, warnings = collect_symbol_candidates(project, ["login_user"], timeout_seconds=2)

    assert warnings == ["rg failed: not found"]
    assert candidates[0].path == Path("auth.py")
