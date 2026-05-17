from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY_PROMPT_ID = "research" "-prompt"


def test_plugin_architecture_doc_describes_public_repo_layout() -> None:
    doc = (ROOT / "docs" / "plugin-architecture.md").read_text(encoding="utf-8")

    for expected in (
        "plugin-sources/",
        "plugin-sources/marketplace.yaml",
        "plugin-sources/shared-skills/",
        "plugins/codex/",
        "plugins/claude/",
        "local-docs/",
        "Do not edit generated",
        "python tools/build_plugins.py",
        "python tools/validate_generated.py",
        "full tree materialization is implemented",
        "`session-memory`, `quality-guard`, `shared-skills`, `shared-subagents`, and `harness-foundry`",
        "_packages/",
        "deep-research-prompt-export",
        "requirements-packet",
        "test-adequacy-reviewer",
        "docs/shared-workflow/AGENTS.block.md",
    ):
        assert expected in doc

    assert f"`{LEGACY_PROMPT_ID}`" not in doc


def test_migration_guide_documents_harness_specific_paths() -> None:
    doc = (ROOT / "docs" / "migration-guide.md").read_text(encoding="utf-8")

    for expected in (
        "plugins/session-memory",
        "plugins/codex/session-memory",
        "plugins/claude/session-memory",
        "No Compatibility Directories",
        "public plugin IDs",
        "migration target",
        "Flat plugin directories are not current generated artifacts",
        "Older flat directories may appear in history",
        "plugin-sources/marketplace.yaml",
    ):
        assert expected in doc

    assert "No compatibility directories are created" not in doc


def test_migration_guide_contains_legacy_mapping() -> None:
    text = (ROOT / "docs" / "migration-guide.md").read_text(encoding="utf-8")

    assert "research-prompt -> deep-research-prompt-export" in text
    assert "requirements-clarifier -> requirements-packet" in text
    assert "spec-reviewer -> requirements-reviewer + plan-reviewer" in text
