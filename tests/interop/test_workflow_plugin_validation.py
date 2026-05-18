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
    REQUIRED_LANGUAGE_TEST_SMELL_TERMS,
    REQUIRED_SHARED_SKILL_SCHEMA_HEADERS,
    REQUIRED_SHARED_SKILL_REFERENCES,
    REQUIRED_SHARED_SUBAGENTS,
    REQUIRED_TEST_ASSERTION_QUALITY_TERMS,
    REQUIRED_TEST_ARTIFACT_DRIFT_TERMS,
    REQUIRED_TEST_RELEVANCE_TERMS,
    REQUIRED_WORKFLOW_ARTIFACT_TERMS,
    validate_workflow_plugins,
)


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated test artifact\n", encoding="utf-8")


def write_minimal_workflow_plugin_shape(root: Path) -> None:
    for harness in ("codex", "claude"):
        references_root = root / "plugins" / harness / "shared-skills" / "references"
        references_root.mkdir(parents=True, exist_ok=True)
        source_references_root = ROOT / "plugins" / harness / "shared-skills" / "references"
        for reference in REQUIRED_SHARED_SKILL_REFERENCES:
            (references_root / reference).write_text(
                (source_references_root / reference).read_text(encoding="utf-8"),
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
    assert "test-relevance-decisions.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "test-artifact-drift.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "test-assertion-quality.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "language-test-smells.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "testing-patterns.md" in REQUIRED_SHARED_SKILL_REFERENCES
    assert "requirements-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "plan-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "spec-coverage-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "completion-claim-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "test-reconciliation-reviewer" in REQUIRED_SHARED_SUBAGENTS
    assert "changed_files" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Spec Ledger" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Spec-to-Plan Coverage Matrix" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "orphan_task" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "needs_spec_mapping" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_plan" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_validation" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_fallback" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_evidence" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "stale_evidence" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "unresolved_risk" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "not_run_hidden" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "missing_review_gate" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "Coverage Report" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "coverage_report_id" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "validator_command" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "validator_exit_code" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "report_path" in REQUIRED_WORKFLOW_ARTIFACT_TERMS
    assert "used_for_claim_ids" in REQUIRED_DEEP_RESEARCH_TERMS
    assert "Fixture/Mock Justification" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "downstream application project" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Behavior Boundary Classification" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Assertion Quality Gate" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "TDD Quality Evidence" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "test-assertion-quality.md" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "language-test-smells.md" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "testing-patterns.md" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "explicit artifact contract" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "behavior_boundary" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "public_entrypoint" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "observable_result" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "assertion_strategy" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "fixture_mock_policy" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "determinism_policy" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "test_smell_risk" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Scenario Change Map" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "linked_scenario_ids" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "relationship_to_current_requirement" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "required_action" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Current Requirement Coverage Contract" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "coverage_status" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "replacement_coverage" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "blocking_risks" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "TDD Cycle Evidence" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Join Rules" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Fixture Governance Contract" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "unjustified_fixture" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "stale_fixture" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "fixture_overgrowth" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "unapproved_mock" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "missing_real_boundary_check" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "test_only_behavior" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "test_artifact_drift_unresolved" in REQUIRED_DOWNSTREAM_TEST_TERMS
    assert "Existing Test Relevance Inventory" in REQUIRED_TEST_RELEVANCE_TERMS
    assert "quarantine" in REQUIRED_TEST_RELEVANCE_TERMS
    assert "Test Artifact Drift Inventory" in REQUIRED_TEST_ARTIFACT_DRIFT_TERMS
    assert "no_artifact_expected" in REQUIRED_TEST_ARTIFACT_DRIFT_TERMS
    for smell_code in (
        "weak_assertion",
        "mock_only_assertion",
        "private_behavior_test",
        "implementation_detail_assertion",
        "broad_snapshot",
        "non_diagnostic_failure",
        "wrong_layer",
        "flaky_shared_state",
        "coverage_theater",
    ):
        assert smell_code in REQUIRED_TEST_ASSERTION_QUALITY_TERMS
        assert smell_code in REQUIRED_LANGUAGE_TEST_SMELL_TERMS


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
        ("workflow-artifacts.md", "missing_fallback"),
        ("workflow-artifacts.md", "missing_evidence"),
        ("workflow-artifacts.md", "stale_evidence"),
        ("workflow-artifacts.md", "unresolved_risk"),
        ("workflow-artifacts.md", "not_run_hidden"),
        ("workflow-artifacts.md", "missing_review_gate"),
        ("workflow-artifacts.md", "orphan_task"),
        ("workflow-artifacts.md", "needs_spec_mapping"),
        ("workflow-artifacts.md", "Coverage Report"),
        ("workflow-artifacts.md", "coverage_report_id"),
        ("workflow-artifacts.md", "validator_exit_code"),
        ("downstream-test-contracts.md", "unjustified_fixture"),
        ("downstream-test-contracts.md", "downstream application project"),
        ("downstream-test-contracts.md", "Behavior Boundary Classification"),
        ("downstream-test-contracts.md", "Assertion Quality Gate"),
        ("downstream-test-contracts.md", "TDD Quality Evidence"),
        ("downstream-test-contracts.md", "behavior_boundary"),
        ("downstream-test-contracts.md", "public_entrypoint"),
        ("downstream-test-contracts.md", "observable_result"),
        ("downstream-test-contracts.md", "hidden_implementation_details_to_avoid"),
        ("downstream-test-contracts.md", "required_test_layer"),
        ("downstream-test-contracts.md", "why_this_layer_is_narrowest_reliable_layer"),
        ("downstream-test-contracts.md", "assertion_strategy"),
        ("downstream-test-contracts.md", "fixture_mock_policy"),
        ("downstream-test-contracts.md", "determinism_policy"),
        ("downstream-test-contracts.md", "test_smell_risk"),
        ("downstream-test-contracts.md", "intended_failure_reason"),
        ("downstream-test-contracts.md", "why_failure_proves_missing_behavior"),
        ("downstream-test-contracts.md", "assertion_quality_gate"),
        ("downstream-test-contracts.md", "determinism_controls"),
        ("downstream-test-contracts.md", "fixture_mock_justification"),
        ("downstream-test-contracts.md", "Scenario Change Map"),
        ("downstream-test-contracts.md", "scenario_change_id"),
        ("downstream-test-contracts.md", "previous_scenario_or_test_id"),
        ("downstream-test-contracts.md", "linked_scenario_ids"),
        ("downstream-test-contracts.md", "current_acceptance_criteria_id"),
        ("downstream-test-contracts.md", "relationship_to_current_requirement"),
        ("downstream-test-contracts.md", "replacement_or_gap_id"),
        ("downstream-test-contracts.md", "obsolete"),
        ("downstream-test-contracts.md", "missing_current_coverage"),
        ("downstream-test-contracts.md", "not_applicable_with_reason"),
        ("downstream-test-contracts.md", "required_action"),
        ("downstream-test-contracts.md", "keep"),
        ("downstream-test-contracts.md", "replace"),
        ("downstream-test-contracts.md", "manual_or_inspection_evidence"),
        ("downstream-test-contracts.md", "Current Requirement Coverage Contract"),
        ("downstream-test-contracts.md", "coverage_contract_id"),
        ("downstream-test-contracts.md", "current_requirement_id"),
        ("downstream-test-contracts.md", "acceptance_criteria_id"),
        ("downstream-test-contracts.md", "coverage_status"),
        ("downstream-test-contracts.md", "core_evidence"),
        ("downstream-test-contracts.md", "residual_gap"),
        ("downstream-test-contracts.md", "covered"),
        ("downstream-test-contracts.md", "residual_risk_id"),
        ("downstream-test-contracts.md", "replacement_coverage"),
        ("downstream-test-contracts.md", "owner_or_followup"),
        ("downstream-test-contracts.md", "blocking_risks"),
        ("downstream-test-contracts.md", "manual_evidence_not_repeatable"),
        ("downstream-test-contracts.md", "TDD Cycle Evidence"),
        ("downstream-test-contracts.md", "tdd_evidence_id"),
        ("downstream-test-contracts.md", "scenario_id"),
        ("downstream-test-contracts.md", "test_file"),
        ("downstream-test-contracts.md", "Join Rules"),
        ("downstream-test-contracts.md", "stale_fixture"),
        ("downstream-test-contracts.md", "fixture_overgrowth"),
        ("downstream-test-contracts.md", "unapproved_mock"),
        ("downstream-test-contracts.md", "missing_real_boundary_check"),
        ("downstream-test-contracts.md", "test_only_behavior"),
        ("downstream-test-contracts.md", "test_artifact_drift_unresolved"),
        ("test-relevance-decisions.md", "Existing Test Relevance Inventory"),
        ("test-relevance-decisions.md", "quarantine"),
        ("test-artifact-drift.md", "Test Artifact Drift Inventory"),
        ("test-artifact-drift.md", "no_artifact_expected"),
        ("test-assertion-quality.md", "Behavior Boundary Classification"),
        ("test-assertion-quality.md", "Assertion Quality Gate"),
        ("test-assertion-quality.md", "TDD Quality Evidence"),
        ("test-assertion-quality.md", "downstream application project"),
        ("test-assertion-quality.md", "behavior_boundary"),
        ("test-assertion-quality.md", "public_entrypoint"),
        ("test-assertion-quality.md", "observable_result"),
        ("test-assertion-quality.md", "hidden_implementation_details_to_avoid"),
        ("test-assertion-quality.md", "required_test_layer"),
        ("test-assertion-quality.md", "why_this_layer_is_narrowest_reliable_layer"),
        ("test-assertion-quality.md", "assertion_strategy"),
        ("test-assertion-quality.md", "fixture_mock_policy"),
        ("test-assertion-quality.md", "determinism_policy"),
        ("test-assertion-quality.md", "test_smell_risk"),
        ("test-assertion-quality.md", "intended_failure_reason"),
        ("test-assertion-quality.md", "why_failure_proves_missing_behavior"),
        ("test-assertion-quality.md", "assertion_quality_gate"),
        ("test-assertion-quality.md", "determinism_controls"),
        ("test-assertion-quality.md", "fixture_mock_justification"),
        ("test-assertion-quality.md", "weak_assertion"),
        ("test-assertion-quality.md", "mock_only_assertion"),
        ("test-assertion-quality.md", "private_behavior_test"),
        ("test-assertion-quality.md", "implementation_detail_assertion"),
        ("test-assertion-quality.md", "broad_snapshot"),
        ("test-assertion-quality.md", "non_diagnostic_failure"),
        ("test-assertion-quality.md", "wrong_layer"),
        ("test-assertion-quality.md", "flaky_shared_state"),
        ("test-assertion-quality.md", "coverage_theater"),
        ("language-test-smells.md", "downstream application project"),
        ("language-test-smells.md", "behavior_boundary"),
        ("language-test-smells.md", "public_entrypoint"),
        ("language-test-smells.md", "observable_result"),
        ("language-test-smells.md", "assertion_strategy"),
        ("language-test-smells.md", "fixture_mock_policy"),
        ("language-test-smells.md", "determinism_policy"),
        ("language-test-smells.md", "test_smell_risk"),
        ("language-test-smells.md", "weak_assertion"),
        ("language-test-smells.md", "mock_only_assertion"),
        ("language-test-smells.md", "private_behavior_test"),
        ("language-test-smells.md", "implementation_detail_assertion"),
        ("language-test-smells.md", "broad_snapshot"),
        ("language-test-smells.md", "non_diagnostic_failure"),
        ("language-test-smells.md", "wrong_layer"),
        ("language-test-smells.md", "flaky_shared_state"),
        ("language-test-smells.md", "coverage_theater"),
        ("language-test-smells.md", ".NET"),
        ("language-test-smells.md", "JavaScript/TypeScript"),
        ("language-test-smells.md", "Java/Kotlin"),
        ("language-test-smells.md", "SQL/Migration"),
        ("language-test-smells.md", "IaC"),
        ("testing-patterns.md", "downstream application project"),
        ("testing-patterns.md", "observable behavior"),
        ("testing-patterns.md", "explicit artifact contract"),
        ("testing-patterns.md", "test-assertion-quality.md"),
        ("testing-patterns.md", "language-test-smells.md"),
        ("testing-patterns.md", "weak assertions"),
        ("testing-patterns.md", "mock-only assertions"),
        ("testing-patterns.md", "private behavior tests"),
        ("testing-patterns.md", "implementation-detail assertions"),
        ("testing-patterns.md", "broad snapshots"),
        ("testing-patterns.md", "non-diagnostic failures"),
        ("testing-patterns.md", "wrong-layer tests"),
        ("testing-patterns.md", "flaky shared"),
        ("testing-patterns.md", "coverage theater"),
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


@pytest.mark.parametrize(
    ("reference", "header"),
    [
        (reference, header)
        for reference, headers in REQUIRED_SHARED_SKILL_SCHEMA_HEADERS.items()
        for header in headers
    ],
)
def test_workflow_validation_reports_each_missing_schema_header(
    tmp_path: Path,
    reference: str,
    header: str,
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
        target.read_text(encoding="utf-8").replace(header, header.replace("|", ":", 1)),
        encoding="utf-8",
    )

    errors = validate_workflow_plugins(tmp_path)

    assert any(
        "missing shared-skills schema header" in error
        and f"plugins/codex/shared-skills/references/{reference}" in error
        and header in error
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
