from __future__ import annotations

from pathlib import Path

from research_prompt.cli import main


def test_cli_writes_only_codex_prompt_artifact(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text(
        "def run():\n    return 'ok'\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Investigate src/app.py behavior",
            "--path",
            "src/app.py",
            "--date",
            "2026-05-13",
        ]
    )

    assert exit_code == 0
    prompts = list((project / ".codex" / "deep-research-prompts").glob("*.md"))
    assert len(prompts) == 1
    assert not (project / ".claude").exists()
    assert "def run()" in prompts[0].read_text(encoding="utf-8")


def test_cli_writes_only_claude_prompt_artifact(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Sample\n", encoding="utf-8")

    exit_code = main(
        [
            "--project-root",
            str(project),
            "--harness",
            "claude",
            "--problem",
            "Research README structure",
            "--path",
            "README.md",
            "--date",
            "2026-05-13",
        ]
    )

    assert exit_code == 0
    prompts = list((project / ".claude" / "deep-research-prompts").glob("*.md"))
    assert len(prompts) == 1
    assert not (project / ".codex").exists()


def test_cli_refuses_denied_path(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".env").write_text("TOKEN=secret\n", encoding="utf-8")

    exit_code = main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Investigate env",
            "--path",
            ".env",
            "--date",
            "2026-05-13",
        ]
    )

    assert exit_code == 0
    prompt = next((project / ".codex" / "deep-research-prompts").glob("*.md"))
    text = prompt.read_text(encoding="utf-8")
    assert "TOKEN=secret" not in text
    assert "Denied sensitive path: .env" in text


def test_cli_does_not_overwrite_existing_prompt(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    args = [
        "--project-root",
        str(project),
        "--harness",
        "codex",
        "--problem",
        "Repeat prompt",
        "--date",
        "2026-05-13",
    ]

    assert main(args) == 0
    assert main(args) == 0

    prompts = sorted((project / ".codex" / "deep-research-prompts").glob("*.md"))
    assert len(prompts) == 2
    assert {prompt.name for prompt in prompts} == {
        "2026-05-13-repeat-prompt.md",
        "2026-05-13-repeat-prompt-2.md",
    }


def test_cli_denies_path_traversal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET_TOKEN=secret\n", encoding="utf-8")

    assert main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Traversal",
            "--path",
            "../outside.py",
            "--date",
            "2026-05-13",
        ]
    ) == 0

    prompt = next((project / ".codex" / "deep-research-prompts").glob("*.md"))
    text = prompt.read_text(encoding="utf-8")
    assert "SECRET_TOKEN=secret" not in text
    assert "Denied path outside project: ../outside.py" in text


def test_cli_includes_logs_reproduction_and_stack_trace_paths(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "server.py").write_text(
        "def handler():\n    raise RuntimeError()\n",
        encoding="utf-8",
    )
    log_file = project / "failure.log"
    log_file.write_text(
        'Traceback\n  File "src/server.py", line 2, in handler\nRuntimeError: boom\n',
        encoding="utf-8",
    )

    assert main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Investigate runtime failure",
            "--log",
            "failure.log",
            "--repro",
            "Run python src/server.py",
            "--constraint",
            "Do not suggest breaking changes",
            "--goal",
            "Find source-backed root causes",
            "--expected-output",
            "Prioritized fixes with citations",
            "--date",
            "2026-05-13",
        ]
    ) == 0

    prompt = next((project / ".codex" / "deep-research-prompts").glob("*.md"))
    text = prompt.read_text(encoding="utf-8")
    assert "RuntimeError: boom" in text
    assert "src/server.py" in text
    assert "Run python src/server.py" in text
    assert "Do not suggest breaking changes" in text
    assert "Prioritized fixes with citations" in text


def test_cli_respects_budget_and_does_not_create_extra_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "large.py").write_text("x = '0123456789'\n" * 2000, encoding="utf-8")

    assert main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Budget test",
            "--path",
            "large.py",
            "--max-snippet-chars",
            "120",
            "--date",
            "2026-05-13",
        ]
    ) == 0

    prompt_dir = project / ".codex" / "deep-research-prompts"
    prompts = list(prompt_dir.glob("*.md"))
    assert len(prompts) == 1
    text = prompts[0].read_text(encoding="utf-8")
    assert "[TRUNCATED: excerpt exceeded budget]" in text
    assert not (prompt_dir / "latest.md").exists()
    assert not (prompt_dir / "index.json").exists()
    assert not (prompt_dir / "cache.json").exists()


def test_cli_scoped_scan_ignores_unmentioned_large_tree(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "target.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    noise = project / "noise"
    noise.mkdir()
    for index in range(200):
        (noise / f"file_{index}.py").write_text("def noise():\n    return 0\n", encoding="utf-8")

    assert main(
        [
            "--project-root",
            str(project),
            "--harness",
            "codex",
            "--problem",
            "Scoped scan",
            "--path",
            "target.py",
            "--max-snippet-chars",
            "300",
            "--date",
            "2026-05-13",
        ]
    ) == 0

    prompt = next((project / ".codex" / "deep-research-prompts").glob("*.md"))
    text = prompt.read_text(encoding="utf-8")
    assert "def target()" in text
    assert "file_199.py" not in text
