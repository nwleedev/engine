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
        "docs/session-memory/AGENTS.block.md",
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


def test_agents_policy_blocks_are_split_and_compact() -> None:
    session_memory = ROOT / "docs" / "session-memory" / "AGENTS.block.md"
    shared_skills = ROOT / "docs" / "shared-skills" / "AGENTS.block.md"
    shared_subagents = ROOT / "docs" / "shared-subagents" / "AGENTS.block.md"
    legacy = ROOT / "docs" / "shared-workflow" / "AGENTS.block.md"

    session_text = session_memory.read_text(encoding="utf-8")
    skills_text = shared_skills.read_text(encoding="utf-8")
    subagents_text = shared_subagents.read_text(encoding="utf-8")

    assert not legacy.exists()
    assert "## Codex Session Memory" in session_text
    assert "$session-memory:checkpoint" in session_text
    assert "$session-memory:resume" in session_text
    assert "$session-memory:status" in session_text
    assert "CODEX_SESSION_ID" in session_text
    assert "CODEX_THREAD_ID" in session_text
    assert "not as the session-memory artifact destination" in session_text
    assert "<!-- SHARED-SKILLS-START -->" in skills_text
    assert "<!-- SHARED-SUBAGENTS-START -->" in subagents_text
    assert "$session-memory:checkpoint" not in skills_text
    assert "$session-memory:checkpoint" not in subagents_text
    assert "Spawn subagents" not in skills_text
    assert "<!-- SHARED-SUBAGENTS-START -->" not in skills_text
    assert "routing shim" in skills_text
    assert "invoke the matching shared-skills skill and follow its `SKILL.md`" in skills_text
    assert (
        "requirements, research, specs, plans, tests, implementation evidence, or completion claims"
        in skills_text
    )
    assert "implementation-evidence" in skills_text
    assert "verification-gate" in skills_text
    assert "installed shared-skills `SKILL.md` and `references/*`" in skills_text
    assert "install/status diagnostic" in skills_text
    assert skills_text.count("\n- ") <= 6
    assert len(skills_text.encode("utf-8")) <= 1200
    assert "Fixture Governance Contract" not in skills_text
    assert "shared-skills workflow artifacts" not in subagents_text
    assert "Spawn subagents only when the user explicitly asks" in subagents_text
    assert "reviewer/code-reviewer/security-auditor" in subagents_text
    assert "main-session fallback prompts" in subagents_text
    assert "agents.max_depth = 1" in subagents_text
    assert subagents_text.count("\n- ") <= 6
    assert len(subagents_text.encode("utf-8")) <= 1000
    assert "Fixture Governance Contract" not in subagents_text
