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
        "docs/shared-skills/AGENTS.block.md",
        "docs/shared-subagents/AGENTS.block.md",
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


def test_shared_workflow_agents_blocks_are_split_and_compact() -> None:
    shared_skills = ROOT / "docs" / "shared-skills" / "AGENTS.block.md"
    shared_subagents = ROOT / "docs" / "shared-subagents" / "AGENTS.block.md"
    legacy = ROOT / "docs" / "shared-workflow" / "AGENTS.block.md"

    skills_text = shared_skills.read_text(encoding="utf-8")
    subagents_text = shared_subagents.read_text(encoding="utf-8")
    legacy_text = legacy.read_text(encoding="utf-8")

    assert "<!-- SHARED-SKILLS-START -->" in skills_text
    assert "<!-- SHARED-SUBAGENTS-START -->" in subagents_text
    assert "Spawn subagents" not in skills_text
    assert "<!-- SHARED-SUBAGENTS-START -->" not in skills_text
    assert (
        "requirements, research, specs, plans, tests, implementation evidence, or completion claims"
        in skills_text
    )
    assert "installed shared-skills `SKILL.md` and `references/*`" in skills_text
    assert "install/status diagnostic" in skills_text
    assert "shared-skills workflow artifacts" not in subagents_text
    assert "Spawn subagents only when the user explicitly asks" in subagents_text
    assert "reviewer/code-reviewer/security-auditor" in subagents_text
    assert "main-session fallback prompts" in subagents_text
    assert "agents.max_depth = 1" in subagents_text
    assert "migration pointer" in legacy_text.lower()
    assert "docs/shared-skills/AGENTS.block.md" in legacy_text
    assert "docs/shared-subagents/AGENTS.block.md" in legacy_text
