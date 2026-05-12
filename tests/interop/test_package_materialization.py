from __future__ import annotations

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
