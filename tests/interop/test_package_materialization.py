from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_session_memory_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/session-memory/_packages/session_memory/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/session-memory/_packages/session_memory/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/codex/session-memory/_packages/session_memory/jsonl_parser.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/session-memory/_packages/session_memory/evidence_extractor.py"
    ).exists()


def test_quality_guard_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/quality-guard/_packages/quality_guard/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/quality-guard/_packages/quality_guard/__init__.py"
    ).exists()


def test_research_prompt_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/research-prompt/_packages/research_prompt/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/research-prompt/_packages/research_prompt/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/codex/research-prompt/_packages/research_prompt/cli.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/research-prompt/_packages/research_prompt/redaction.py"
    ).exists()


def test_research_prompt_generated_wrappers_run_with_defaults(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    env = {**os.environ, "RESEARCH_PROMPT_DATE": "2026-05-13"}

    subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "plugins/codex/research-prompt/skills/research-prompt/scripts/research_prompt.py"
            ),
            "--harness",
            "codex",
            "--problem",
            "Wrapper defaults",
        ],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugins/claude/research-prompt/scripts/research_prompt.py"),
            "--harness",
            "claude",
            "--problem",
            "Wrapper defaults",
        ],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        project / ".codex/deep-research-prompts/2026-05-13-wrapper-defaults.md"
    ).exists()
    assert (
        project / ".claude/deep-research-prompts/2026-05-13-wrapper-defaults.md"
    ).exists()
