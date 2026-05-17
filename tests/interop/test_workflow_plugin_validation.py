from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_workflow_plugins import (
    FORBIDDEN_LEGACY_NAMES,
    REQUIRED_DEEP_RESEARCH_TERMS,
    REQUIRED_DOWNSTREAM_TEST_TERMS,
    REQUIRED_SHARED_SKILL_REFERENCES,
    REQUIRED_SHARED_SUBAGENTS,
    REQUIRED_WORKFLOW_ARTIFACT_TERMS,
    validate_workflow_plugins,
)


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated test artifact\n", encoding="utf-8")


def write_minimal_workflow_plugin_shape(root: Path) -> None:
    for harness in ("codex", "claude"):
        references_root = root / "plugins" / harness / "shared-skills" / "references"
        (references_root / "workflow-artifacts.md").parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        (references_root / "workflow-artifacts.md").write_text(
            "\n".join(REQUIRED_WORKFLOW_ARTIFACT_TERMS),
            encoding="utf-8",
        )
        (references_root / "deep-research-pipeline.md").write_text(
            "\n".join(REQUIRED_DEEP_RESEARCH_TERMS),
            encoding="utf-8",
        )
        (references_root / "downstream-test-contracts.md").write_text(
            "\n".join(REQUIRED_DOWNSTREAM_TEST_TERMS),
            encoding="utf-8",
        )

    for agent in REQUIRED_SHARED_SUBAGENTS:
        touch(root / "plugins" / "codex" / "shared-subagents" / "agents" / f"{agent}.toml")
        touch(root / "plugins" / "claude" / "shared-subagents" / "agents" / f"{agent}.md")


def test_workflow_validation_constants_cover_retired_routes_and_contracts() -> None:
    assert "requirements-clarifier" in FORBIDDEN_LEGACY_NAMES
    assert "online-researcher" in FORBIDDEN_LEGACY_NAMES
    assert "workflow-artifacts.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "downstream-test-contracts.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "requirements-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "plan-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "spec-coverage-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "completion-claim-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "changed_files" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Spec Ledger" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Spec-to-Plan Coverage Matrix" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_plan" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_validation" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_evidence" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "stale_evidence" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "unresolved_risk" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Coverage Report" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "coverage_report_id" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "validator_command" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "validator_exit_code" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "report_path" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "used_for_claim_ids" in REQUIRED_DEEP_RESEARCH_TERMS
    assert "Fixture/Mock Justification" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Fixture Governance Contract" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "unjustified_fixture" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "fixture_overgrowth" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "missing_real_boundary_check" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "test_only_behavior" in REQUIRED_DOWNSTREAM_TEST_TERMS


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


def test_workflow_validation_reports_missing_schema_terms(tmp_path: Path) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    workflow_reference = (
        tmp_path
        / "plugins"
        / "codex"
        / "shared-skills"
        / "references"
        / "workflow-artifacts.md"
    )
    workflow_reference.write_text("Requirement Packet\n", encoding="utf-8")

    errors = validate_workflow_plugins(tmp_path)

    assert any(
        "missing shared-skills schema term" in error
        and "plugins/codex/shared-skills/references/workflow-artifacts.md" in error
        and "changed_files" in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("reference", "term"),
    [
        ("workflow-artifacts.md", "missing_plan"),
        ("workflow-artifacts.md", "missing_validation"),
        ("workflow-artifacts.md", "missing_evidence"),
        ("workflow-artifacts.md", "stale_evidence"),
        ("workflow-artifacts.md", "unresolved_risk"),
        ("workflow-artifacts.md", "Coverage Report"),
        ("workflow-artifacts.md", "coverage_report_id"),
        ("workflow-artifacts.md", "validator_exit_code"),
        ("downstream-test-contracts.md", "unjustified_fixture"),
        ("downstream-test-contracts.md", "fixture_overgrowth"),
        ("downstream-test-contracts.md", "missing_real_boundary_check"),
        ("downstream-test-contracts.md", "test_only_behavior"),
    ],
)
def test_workflow_validation_reports_each_missing_blocking_term(
    tmp_path: Path,
    reference: str,
    term: str,
) -> None:
    write_minimal_workflow_plugin_shape(tmp_path)
    target = (
        tmp_path
        / "plugins"
        / "codex"
        / "shared-skills"
        / "references"
        / reference
    )
    target.write_text(
        target.read_text(encoding="utf-8").replace(term, ""),
        encoding="utf-8",
    )

    errors = validate_workflow_plugins(tmp_path)

    assert any(
        "missing shared-skills schema term" in error
        and f"plugins/codex/shared-skills/references/{reference}" in error
        and term in error
        for error in errors
    )


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
