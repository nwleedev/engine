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
