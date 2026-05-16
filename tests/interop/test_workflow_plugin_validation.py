from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_workflow_plugins import (
    FORBIDDEN_LEGACY_NAMES,
    REQUIRED_SHARED_SKILL_REFERENCES,
    validate_workflow_plugins,
)


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated test artifact\n", encoding="utf-8")


def write_minimal_workflow_plugin_shape(root: Path) -> None:
    for harness in ("codex", "claude"):
        for reference in REQUIRED_SHARED_SKILL_REFERENCES:
            touch(root / "plugins" / harness / "shared-skills" / "references" / reference)

    for agent in ("test-adequacy-reviewer", "closure-reviewer"):
        touch(root / "plugins" / "codex" / "shared-subagents" / "agents" / f"{agent}.toml")
        touch(root / "plugins" / "claude" / "shared-subagents" / "agents" / f"{agent}.md")


def test_workflow_validation_constants_cover_retired_routes_and_contracts() -> None:
    assert "requirements-clarifier" in FORBIDDEN_LEGACY_NAMES
    assert "online-researcher" in FORBIDDEN_LEGACY_NAMES
    assert "workflow-artifacts.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "downstream-test-contracts.md" in REQUIRED_SHARED_SKILL_REFERENCES


def test_workflow_validation_reports_legacy_generated_artifact_path(
    tmp_path: Path,
) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    legacy_path = (
        tmp_path
        / "plugins"
        / "codex"
        / "shared-skills"
        / "skills"
        / "requirements-clarifier"
        / "SKILL.md"
    )
    touch(legacy_path)

    errors = validate_workflow_plugins(tmp_path)

    assert any(
        "legacy generated artifact" in error
        and "requirements-clarifier" in error
        and "plugins/codex/shared-skills/skills/requirements-clarifier/SKILL.md"
        in error
        for error in errors
    )


def test_workflow_validation_accepts_minimal_codex_and_claude_shape(
    tmp_path: Path,
) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    touch(
        tmp_path
        / "plugins"
        / "codex"
        / "custom-plugin"
        / "skills"
        / "requirements-clarifier"
        / "SKILL.md"
    )

    assert validate_workflow_plugins(tmp_path) == []


def test_workflow_validation_reports_exact_missing_required_artifact_errors(
    tmp_path: Path,
) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    (
        tmp_path
        / "plugins"
        / "claude"
        / "shared-skills"
        / "references"
        / "workflow-artifacts.md"
    ).unlink()
    (
        tmp_path
        / "plugins"
        / "codex"
        / "shared-subagents"
        / "agents"
        / "closure-reviewer.toml"
    ).unlink()

    errors = validate_workflow_plugins(tmp_path)

    assert (
        "missing required shared-skills reference for claude: "
        "plugins/claude/shared-skills/references/workflow-artifacts.md"
    ) in errors
    assert (
        "missing required shared-subagents agent for codex: "
        "plugins/codex/shared-subagents/agents/closure-reviewer.toml"
    ) in errors


def test_workflow_validation_ignores_passive_legacy_support_reference_paths(
    tmp_path: Path,
) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    touch(
        tmp_path
        / "plugins"
        / "codex"
        / "shared-skills"
        / "references"
        / "requirements-clarifier"
        / "notes.md"
    )

    errors = validate_workflow_plugins(tmp_path)

    assert not any("legacy generated artifact" in error for error in errors)
