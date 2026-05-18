from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path("plugins/codex/shared-skills")
CLAUDE_PLUGIN_ROOT = Path("plugins/claude/shared-skills")
SHARED_SKILLS_BLOCK = Path("docs/shared-skills/AGENTS.block.md")
SKILLS = (
    "requirements-packet",
    "spec-contract",
    "plan-contract",
    "implementation-evidence",
    "verification-gate",
    "research-plan",
    "source-ledger",
    "claim-evidence-map",
    "testing-workflow",
    "scenario-test-designer",
    "test-suite-reconciliation",
    "test-plan-contract",
    "tdd-cycle",
    "spec-plan-coverage",
    "comment-writing",
    "implementation-discipline",
    "debugging-discipline",
)
LEGACY_SKILLS = (
    "requirements-clarifier",
    "research-crosscheck",
    "task-planner",
    "review-checklist",
    "verification-evidence",
)


def read(path: Path) -> str:
    """Read a UTF-8 text file from the repository."""

    return path.read_text(encoding="utf-8")


def section_body(text: str, heading: str) -> str:
    """Return the body until the next Markdown level-two heading line."""

    lines = text.splitlines()
    start_heading = f"## {heading}"
    start_index = lines.index(start_heading) + 1
    end_index = len(lines)

    for index in range(start_index, len(lines)):
        if lines[index].startswith("## "):
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def test_manifest_exposes_shared_skills_plugin() -> None:
    manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

    manifest = json.loads(read(manifest_path))

    assert manifest["name"] == "shared-skills"
    assert manifest["version"] == "0.2.9"
    assert manifest["license"] == "MIT"
    assert manifest["skills"] == "./skills/"
    assert "requirements traceability" in manifest["description"]
    assert "scenario-based tests" in manifest["description"]


def test_all_lean_core_skills_exist_with_frontmatter() -> None:
    for skill_name in SKILLS:
        skill_path = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        text = read(skill_path)
        source_path = f"plugin-sources/shared-skills/skills/{skill_name}/SKILL.md"

        assert text.startswith("---\n")
        assert f"\n---\n<!-- GENERATED FILE - DO NOT EDIT -->\n<!-- source: {source_path} -->\n\n" in text
        assert f"name: {skill_name}" in text
        assert "description: Use when" in text
        assert "metadata:\n  short-description:" in text
        assert "\n---\n" in text


def test_skills_cover_development_and_non_development_work() -> None:
    for skill_name in SKILLS:
        text = read(PLUGIN_ROOT / "skills" / skill_name / "SKILL.md")

        assert "Workflow" in text
        assert "Development work" in text
        assert "Non-development work" in text
        assert "Output" in text
        assert "Do not" in text


def test_legacy_shared_skills_are_not_generated() -> None:
    for skill_name in LEGACY_SKILLS:
        assert not (PLUGIN_ROOT / "skills" / skill_name).exists()

    combined = "\n".join(
        read(path)
        for path in sorted(PLUGIN_ROOT.rglob("*"))
        if path.is_file() and path.suffix in {".md", ".json"}
    )

    for skill_name in LEGACY_SKILLS:
        assert f"$shared-skills:{skill_name}" not in combined


def test_workflow_artifact_reference_defines_required_ids() -> None:
    text = read(PLUGIN_ROOT / "references" / "workflow-artifacts.md")
    expected_headers = (
        "| spec_clause_id | linked_requirement_ids | source_location | clause_type | validation_intent | priority | confidentiality | status | notes |",
        "| task_id | linked_requirement_ids | linked_spec_clause_ids | steps | target_files_or_artifacts | validation_method | done_criteria | fallback | risk_level |",
        "| spec_clause_id | linked_requirement_ids | plan_task_ids | scenario_ids | test_or_check_ids | evidence_ids | coverage_status | gap_or_risk | owner |",
        "| coverage_report_id | matrix_id | validator_command | validator_exit_code | report_path | redacted_markdown_path | blocking_codes | final_status |",
    )

    required_terms = (
        "Requirement Packet",
        "requirement_id",
        "Spec Contract",
        "spec_id",
        "Spec Ledger",
        "spec_clause_id",
        "source_location",
        "validation_intent",
        "Plan Contract",
        "task_id",
        "linked_spec_clause_ids",
        "steps",
        "done_criteria",
        "risk_level",
        "Spec-to-Plan Coverage Matrix",
        "coverage_status",
        "orphan_task",
        "needs_spec_mapping",
        "missing_plan",
        "missing_validation",
        "missing_fallback",
        "missing_evidence",
        "stale_evidence",
        "unresolved_risk",
        "not_run_hidden",
        "missing_review_gate",
        "Coverage Report",
        "coverage_report_id",
        "validator_command",
        "validator_exit_code",
        "report_path",
        "redacted_markdown_path",
        "blocking_codes",
        "Traceability Matrix",
        "changed_files",
        "test_or_check_ids",
        "Implementation Evidence",
        "Verification Gate",
    )
    for header in expected_headers:
        assert header in text
    for term in required_terms:
        assert term in text

    for status in (
        "covered",
        "missing_plan",
        "missing_validation",
        "missing_evidence",
        "stale_evidence",
        "unresolved_risk",
        "deferred_with_owner",
        "not_applicable_with_reason",
    ):
        assert status in text


def test_workflow_skill_outputs_use_canonical_schema_headers() -> None:
    requirements_text = read(
        PLUGIN_ROOT / "skills" / "requirements-packet" / "SKILL.md"
    )
    implementation_text = read(
        PLUGIN_ROOT / "skills" / "implementation-evidence" / "SKILL.md"
    )

    assert (
        "| requirement_id | status | requirement | source_text | acceptance_criteria | non_goal | assumption_or_question |"
        in requirements_text
    )
    assert (
        "| evidence_id | linked_requirement_ids | linked_spec_clause_ids | linked_task_ids | files_changed | behavior_changed | commands_run | result |"
        in implementation_text
    )


def test_downstream_test_contract_limits_fixture_and_mock_use() -> None:
    text = read(PLUGIN_ROOT / "references" / "downstream-test-contracts.md")
    scenario_change = section_body(text, "Scenario Change Map")
    current_coverage = section_body(text, "Current Requirement Coverage Contract")
    tdd_evidence = section_body(text, "TDD Cycle Evidence")
    quality_evidence = section_body(text, "TDD Quality Evidence")
    join_rules = section_body(text, "Join Rules")

    assert (
        "| fixture_id | linked_scenario_ids | linked_spec_clause_ids | fixture_type | real_boundary_preferred | justification | owner | drift_check | expiry_or_update_trigger |"
        in text
    )
    assert (
        "| scenario_id | previous_acceptance_criteria | current_acceptance_criteria | scenario_status | affected_tests | required_action |"
        in scenario_change
    )
    assert "Scenario Change Map Extension" in scenario_change
    assert (
        "| scenario_id | previous_scenario_or_test_id | relationship_to_current_requirement | replacement_or_gap_id | reconciliation_id |"
        in scenario_change
    )
    for term in (
        "relationship_to_current_requirement",
        "required_action",
        "still_valid",
        "partially_valid",
        "obsolete",
        "contradicts_current_requirement",
        "missing_current_coverage",
        "not_applicable_with_reason",
        "keep",
        "update",
        "split",
        "replace",
        "demote",
        "delete",
        "quarantine",
        "add_new_coverage",
        "manual_or_inspection_evidence",
    ):
        assert term in scenario_change
    assert (
        "| coverage_id | acceptance_criteria_id | behavior_boundary | reconciliation_decision_ids | required_test_changes | required_artifact_changes | required_new_tests | commands | evidence_ids | blocking_risks |"
        in current_coverage
    )
    assert "Current Requirement Coverage Extension" in current_coverage
    assert (
        "| coverage_id | reconciliation_id | current_requirement_id | linked_scenario_ids | coverage_status | core_evidence | residual_gap | residual_risk_id | manual_or_inspection_evidence | replacement_coverage | owner_or_followup |"
        in current_coverage
    )
    for term in (
        "coverage_status",
        "covered",
        "covered_with_manual_evidence",
        "partial_gap",
        "replacement_required",
        "blocked_by_risk",
        "not_applicable_with_reason",
        "residual_risk_id",
        "manual_or_inspection_evidence",
        "replacement_coverage",
        "owner_or_followup",
        "blocking_risks",
        "none",
        "stale_test_counted_as_core",
        "test_artifact_drift_unresolved",
        "unjustified_fixture",
        "missing_real_boundary_check",
        "test_only_behavior",
        "missing_current_coverage",
        "manual_evidence_not_repeatable",
    ):
        assert term in current_coverage
    assert (
        "| downstream application project | Acceptance Criteria ID | User Scenario ID | behavior_boundary | public_entrypoint | observable_result | test_layer | test_file | test_command | assertion_strategy | fixture_mock_policy | determinism_policy | test_smell_risk |"
        in text
    )
    assert (
        "| evidence_id | reconciliation_id | scenario_id | acceptance_criteria_id | failing_command | observed_failure | passing_command | observed_result | residual_gap |"
        in tdd_evidence
    )
    assert (
        "| evidence_id | behavior_boundary | public_entrypoint | observable_result | intended_failure_reason | why_failure_proves_missing_behavior | assertion_quality_gate | determinism_controls | fixture_mock_justification |"
        in quality_evidence
    )
    for term in (
        "failing_command",
        "observed_failure",
        "passing_command",
        "observed_result",
    ):
        assert term in tdd_evidence
    for term in (
        "Scenario Change Map.scenario_id",
        "Current Requirement Coverage Extension.linked_scenario_ids",
        "TDD Cycle Evidence.scenario_id",
        "reconciliation_id",
    ):
        assert term in join_rules
    assert "downstream project" in text
    assert "Acceptance Criteria ID" in text
    assert "User Scenario ID" in text
    assert "Fixture/Mock Justification" in text
    assert "Fixture Governance Contract" in text
    assert "fixture_id" in text
    assert "real_boundary_preferred" in text
    assert "drift_check" in text
    assert "expiry_or_update_trigger" in text
    assert "unjustified_fixture" in text
    assert "fixture_overgrowth" in text
    assert "unapproved_mock" in text
    assert "missing_real_boundary_check" in text
    assert "test_only_behavior" in text
    assert "Artifact Drift Contract" in text
    assert "expectation_status" in text
    assert "no_artifact_expected" in text
    assert "no_existing_artifact_found" in text
    assert "test_artifact_drift_unresolved" in text
    assert "Do not assert only mock calls" in text
    assert "Do not create broad fixture factories" in text
    assert "observable behavior" in text
    for term in (
        "Behavior Boundary Classification",
        "Assertion Quality Gate",
        "TDD Quality Evidence",
        "downstream application project",
        "behavior_boundary",
        "public_entrypoint",
        "observable_result",
        "assertion_strategy",
        "fixture_mock_policy",
        "determinism_policy",
        "test_smell_risk",
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
        assert term in text


def test_test_quality_references_define_assertion_gate_and_language_smells() -> None:
    assertion_quality = read(PLUGIN_ROOT / "references" / "test-assertion-quality.md")
    language_smells = read(PLUGIN_ROOT / "references" / "language-test-smells.md")

    for text in (assertion_quality, language_smells):
        assert "downstream application project" in text
        for term in (
            "behavior_boundary",
            "public_entrypoint",
            "observable_result",
            "assertion_strategy",
            "fixture_mock_policy",
            "determinism_policy",
            "test_smell_risk",
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
            assert term in text

    assert "Behavior Boundary Classification" in assertion_quality
    assert "Assertion Quality Gate" in assertion_quality
    assert "TDD Quality Evidence" in assertion_quality
    assert (
        "| evidence_id | behavior_boundary | public_entrypoint | observable_result | intended_failure_reason | why_failure_proves_missing_behavior | assertion_quality_gate | determinism_controls | fixture_mock_justification |"
        in assertion_quality
    )
    for stack in (
        "Python",
        "JavaScript/TypeScript",
        "Java/Kotlin",
        ".NET",
        "Go",
        "Rust",
        "SQL/Migration",
        "IaC",
    ):
        assert stack in language_smells
        assert f"| {stack} |" in language_smells


def test_reconciliation_references_define_decisions_and_artifact_drift() -> None:
    decisions = read(PLUGIN_ROOT / "references" / "test-relevance-decisions.md")
    drift = read(PLUGIN_ROOT / "references" / "test-artifact-drift.md")

    assert "Decision Schema" in decisions
    assert "Existing Test Relevance Inventory" in decisions
    for decision in ("keep", "update", "split", "move", "demote", "delete", "quarantine"):
        assert f"`{decision}`" in decisions

    assert "Expectation Schema" in drift
    assert "Test Artifact Drift Inventory" in drift
    for term in (
        "expectation_status",
        "no_artifact_expected",
        "no_existing_artifact_found",
        "schema example",
        "benchmark baseline",
        "IaC expected output",
        "test_artifact_drift_unresolved",
    ):
        assert term in drift


def test_shared_skills_agents_block_is_compact_routing_layer() -> None:
    text = read(SHARED_SKILLS_BLOCK)
    detailed_terms = (
        "Spec Ledger",
        "spec_clause_id",
        "Spec-to-Plan Coverage Matrix",
        "Fixture Governance Contract",
        "fixture budget",
        "unjustified_fixture",
        "fixture_overgrowth",
        "unapproved_mock",
        "stale_fixture",
        "missing_real_boundary_check",
        "test_only_behavior",
    )

    assert "<!-- SHARED-SKILLS-START -->" in text
    assert "<!-- SHARED-SKILLS-END -->" in text
    assert "routing shim" in text
    assert "invoke the matching shared-skills skill and follow its `SKILL.md`" in text
    for routing_term in (
        "requirements",
        "research",
        "specs",
        "plans",
        "tests",
        "implementation evidence",
        "completion claims",
    ):
        assert routing_term in text
    assert "spec-plan-coverage" in text
    assert "research-plan" in text
    assert "source-ledger" in text
    assert "claim-evidence-map" in text
    assert "testing-workflow" in text
    assert "scenario-test-designer" in text
    assert "test-suite-reconciliation" in text
    assert "test-plan-contract" in text
    assert "tdd-cycle" in text
    assert "test-adequacy-reviewer" in text
    assert "test-reconciliation-reviewer" in text
    assert "implementation-discipline" in text
    assert "debugging-discipline" in text
    assert "comment-writing" in text
    assert "implementation-evidence" in text
    assert "verification-gate" in text
    assert "open questions" in text
    assert "counterevidence review" in text
    assert "before claiming work is complete" in text
    assert "installed shared-skills `SKILL.md` and `references/*`" in text
    assert "install/status diagnostic" in text
    assert text.count("\n- ") <= 6
    assert len(text.encode("utf-8")) <= 1500
    for term in detailed_terms:
        assert term not in text


def test_shared_skills_workflow_skills_point_to_workflow_artifact_reference() -> None:
    for skill_name in (
        "requirements-packet",
        "spec-contract",
        "plan-contract",
        "spec-plan-coverage",
        "implementation-evidence",
        "verification-gate",
    ):
        text = read(PLUGIN_ROOT / "skills" / skill_name / "SKILL.md")

        assert "../../references/workflow-artifacts.md" in text
        assert "when table schemas, row-level rules, or coverage status values are needed" in text


def test_shared_skills_test_skills_point_to_downstream_test_reference() -> None:
    for skill_name in (
        "testing-workflow",
        "scenario-test-designer",
        "test-suite-reconciliation",
        "test-plan-contract",
        "tdd-cycle",
    ):
        text = read(PLUGIN_ROOT / "skills" / skill_name / "SKILL.md")

        assert "../../references/downstream-test-contracts.md" in text
        assert "when fixture governance" in text
        assert "scenario mapping" in text
        assert "test contract details are needed" in text


def test_tdd_and_test_plan_contracts_include_behavior_quality_fields() -> None:
    tdd_text = read(PLUGIN_ROOT / "skills" / "tdd-cycle" / "SKILL.md")
    plan_text = read(PLUGIN_ROOT / "skills" / "test-plan-contract" / "SKILL.md")

    for text in (tdd_text, plan_text):
        assert "downstream application project" in text
        assert "../../references/test-assertion-quality.md" in text
        assert "../../references/language-test-smells.md" in text
        assert "observable behavior" in text
        assert "explicit artifact contract" in text
        for term in (
            "behavior_boundary",
            "public_entrypoint",
            "observable_result",
            "assertion_strategy",
            "fixture_mock_policy",
            "determinism_policy",
            "test_smell_risk",
        ):
            assert term in text

    for section in (
        "Behavior Boundary Classification",
        "Assertion Quality Gate",
        "TDD Quality Evidence",
    ):
        assert section in tdd_text

    assert (
        "| behavior_boundary | public_entrypoint | observable_result | hidden_implementation_details_to_avoid | required_test_layer | why_this_layer_is_narrowest_reliable_layer |"
        in tdd_text
    )
    assert (
        "| evidence_id | behavior_boundary | public_entrypoint | observable_result | intended_failure_reason | why_failure_proves_missing_behavior | assertion_quality_gate | determinism_controls | fixture_mock_justification |"
        in tdd_text
    )
    assert (
        "| downstream application project | Acceptance Criteria ID | User Scenario ID | behavior_boundary | public_entrypoint | observable_result | test_layer | test_file | test_command | assertion_strategy | fixture_mock_policy | determinism_policy | test_smell_risk |"
        in tdd_text
    )
    assert (
        "| scenario_id | acceptance_criteria_id | linked_spec_clause_ids | behavior_boundary | public_entrypoint | observable_result | test_layer | test_file | test_command | assertion_strategy | fixture_mock_policy | determinism_policy | test_smell_risk | fixture_governance_ids | evidence_id |"
        in plan_text
    )


def test_test_suite_reconciliation_skill_defines_required_contracts() -> None:
    text = read(PLUGIN_ROOT / "skills" / "test-suite-reconciliation" / "SKILL.md")

    for step in (
        "Requirement Change Detection",
        "Affected Test and Artifact Discovery",
        "Existing Test Relevance Classification",
        "Test Artifact Drift Classification",
        "Acceptance Criteria Traceability Matrix",
        "Assertion Quality Revalidation",
        "Determinism and Flakiness Revalidation",
        "Coverage Gap After Reconciliation",
        "Removal, Demotion, and Quarantine Evidence",
        "Reconciliation Contract",
    ):
        assert step in text

    for output_schema in (
        "Existing Test Relevance Inventory",
        "Test Artifact Drift Inventory",
        "Coverage Gap After Reconciliation",
    ):
        assert output_schema in text

    for decision in ("keep", "update", "split", "move", "demote", "delete", "quarantine"):
        assert f"`{decision}`" in text

    for expectation_status in (
        "expected",
        "expectation_status",
        "no_artifact_expected",
        "unknown_expected",
        "found",
        "no_existing_artifact_found",
    ):
        assert expectation_status in text

    sample_row = (
        "| ART-001 | snapshot |  | TEST-001 | core evidence artifact | "
        "expected | reviewed_current | keep |  |  |"
    )
    assert sample_row in text
    assert (
        "| ART-001 | snapshot |  | TEST-001 | artifact required | "
        "reviewed_current | no_drift |  |  |  |  |"
    ) not in text

    decisions = read(PLUGIN_ROOT / "references" / "test-relevance-decisions.md")
    assert (
        "| TEST-001 | tests/example_test.py | AC-001 | old error is accepted | "
        "new error is rejected | update | assertion still targets obsolete behavior | "
        "false_confidence_test | test-plan-contract |"
    ) in decisions
    assert (
        "| TEST-001 | tests/example_test.py | AC-001 | old error is accepted | "
        "new error is rejected | update | assertion still targets obsolete behavior | "
        "obsolete_test_kept | test-plan-contract |"
    ) not in decisions

    for failure_code in (
        "new_test_added_without_reconciliation",
        "stale_test_counted_as_core",
        "contradictory_test_kept",
        "obsolete_test_kept",
        "orphan_test_as_core_coverage",
        "false_confidence_test",
        "test_artifact_drift_unresolved",
        "snapshot_drift_unreviewed",
        "mock_contract_mismatch",
        "quarantined_test_counted_as_evidence",
        "deletion_without_risk_record",
    ):
        assert failure_code in text


def test_testing_workflow_review_only_route_partitions_reviewers() -> None:
    text = read(PLUGIN_ROOT / "skills" / "testing-workflow" / "SKILL.md")

    reconciliation_terms = (
        "reconciliation evidence",
        "existing test relevance",
        "artifact drift",
        "stale/obsolete/contradictory/orphan/false-confidence coverage claims",
        "deletion/demotion/quarantine evidence",
        "reconciliation/current-coverage test plans",
        "test results for that evidence",
    )
    adequacy_terms = (
        "newly written or modified test assertion quality",
        "behavior boundary",
        "fixture/mock justification",
        "determinism",
        "executable test adequacy",
        "new/modified test plans",
        "test results for those tests",
    )

    review_only_row = next(
        line for line in text.splitlines() if line.startswith("| Review Only |")
    )
    assert "`test-reconciliation-reviewer`" in review_only_row
    assert "`test-adequacy-reviewer`" in review_only_row
    for term in reconciliation_terms:
        assert term in review_only_row
    for term in adequacy_terms:
        assert term in review_only_row


def test_testing_workflow_skill_defines_required_routes() -> None:
    text = read(PLUGIN_ROOT / "skills" / "testing-workflow" / "SKILL.md")

    assert "single entry point" in text
    assert "Testing Workflow Route" in text
    assert "../../references/test-assertion-quality.md" in text
    assert "../../references/language-test-smells.md" in text
    assert "../../references/testing-patterns.md" in text
    assert "Behavior Boundary Classification" in text
    assert "Assertion Quality Gate" in text
    assert "TDD Quality Evidence" in text
    assert "explicit artifact contract" in text
    assert "| route | use_when | next_step |" in text
    assert (
        "| route_id | request_summary | behavior_change_type | existing_tests_may_be_affected | selected_route | required_next_skill_or_agent | reason | residual_risk_if_skipped |"
        in text
    )
    assert "| --- | --- | --- | --- | --- | --- | --- | --- |" in text
    assert "| ROUTE-001 |  |  |  |  |  |  |  |" in text
    for route_name in (
        "New Behavior Coverage",
        "Reconciliation Required",
        "Artifact Drift Review",
        "Review Only",
        "Test Inapplicable",
    ):
        assert route_name in text
    for next_step in (
        "scenario-test-designer -> test-plan-contract -> tdd-cycle",
        "test-suite-reconciliation -> test-plan-contract -> tdd-cycle",
        "test-suite-reconciliation",
        "test-reconciliation-reviewer` for reconciliation evidence, existing test relevance, artifact drift",
        "test-adequacy-reviewer",
        "test-plan-contract -> verification-gate",
    ):
        assert next_step in text
    assert "newly written or modified test adequacy" in text
    assert "stale, obsolete, contradictory, orphaned, false-confidence" in text
    for changed_expectation in (
        "public API",
        "schema",
        "migration",
        "bug expectation",
        "security policy",
        "performance budget",
        "generated artifact contract",
    ):
        assert changed_expectation in text


def test_spec_plan_coverage_skill_defines_failure_codes_and_reports() -> None:
    text = read(PLUGIN_ROOT / "skills" / "spec-plan-coverage" / "SKILL.md")

    assert "Spec Ledger" in text
    assert "Spec-to-Plan Coverage Matrix" in text
    assert "linked_spec_clause_ids" in text
    assert "coverage_status" in text
    assert "machine-readable JSON" in text
    assert "redacted Markdown" in text
    assert "missing_plan" in text
    assert "missing_validation" in text
    assert "missing_fallback" in text
    assert "missing_evidence" in text
    assert "stale_evidence" in text
    assert "unresolved_risk" in text
    assert "not_run_hidden" in text
    assert "missing_review_gate" in text
    assert "unjustified_fixture" in text
    assert "stale_fixture" in text
    assert "fixture_overgrowth" in text
    assert "unapproved_mock" in text
    assert "missing_real_boundary_check" in text
    assert "test_only_behavior" in text


def test_tdd_cycle_skill_defines_tdd_workflow() -> None:
    text = read(PLUGIN_ROOT / "skills" / "tdd-cycle" / "SKILL.md")

    assert "Purpose" in text
    assert "When to use" in text
    assert "Inputs to inspect" in text
    assert "Workflow" in text
    assert "Test type decision matrix" in text
    assert "Test writing rules" in text
    assert "Stack detection rules" in text
    assert "Review handoff" in text
    assert "Output" in text
    assert "Do not" in text
    assert "TDD" in text
    assert "behavior or acceptance criteria" in text
    assert "not optional follow-up" in text
    assert "failing test" in text
    assert "detected stack" in text
    assert "flaky" in text
    assert "Arrange-Act-Assert" in text
    assert "reviewer handoff" in text
    assert "Fixture Governance Contract" in text
    assert "fixture budget" in text
    assert "high-fidelity boundary" in text
    assert "Behavior Boundary Classification" in text
    assert "Assertion Quality Gate" in text
    assert "TDD Quality Evidence" in text


def test_scenario_test_designer_defines_change_map_schema() -> None:
    text = read(PLUGIN_ROOT / "skills" / "scenario-test-designer" / "SKILL.md")

    assert "Scenario Change Map" in text
    for term in (
        "scenario_id",
        "previous_acceptance_criteria",
        "current_acceptance_criteria",
        "scenario_status",
        "affected_tests",
        "previous_scenario_or_test_id",
        "relationship_to_current_requirement",
        "required_action",
        "replacement_or_gap_id",
        "reconciliation_id",
    ):
        assert term in text
    assert "canonical allowed values and join rules" in text
    assert "before new test contracts are created" in text


def test_test_plan_contract_defines_current_requirement_coverage() -> None:
    text = read(PLUGIN_ROOT / "skills" / "test-plan-contract" / "SKILL.md")

    assert "Current Requirement Coverage Contract" in text
    for field in (
        "coverage_id",
        "reconciliation_decision_ids",
        "required_test_changes",
        "required_artifact_changes",
        "required_new_tests",
        "commands",
        "evidence_ids",
        "reconciliation_id",
        "current_requirement_id",
        "acceptance_criteria_id",
        "linked_scenario_ids",
        "coverage_status",
        "core_evidence",
        "residual_gap",
        "residual_risk_id",
        "manual_or_inspection_evidence",
        "replacement_coverage",
        "owner_or_followup",
        "blocking_risks",
    ):
        assert field in text
    assert "canonical allowed values and join rules" in text


def test_tdd_cycle_reconciliation_gate_and_evidence_schema() -> None:
    text = read(PLUGIN_ROOT / "skills" / "tdd-cycle" / "SKILL.md")

    assert "TDD Cycle Evidence" in text
    assert (
        "| evidence_id | reconciliation_id | scenario_id | acceptance_criteria_id | failing_command | observed_failure | passing_command | observed_result | residual_gap |"
        in text
    )
    assert "canonical join rules" in text
    assert "do not add a new test until" in text
    assert "Current Requirement Coverage Contract" in read(
        PLUGIN_ROOT / "skills" / "verification-gate" / "SKILL.md"
    )
    assert "TDD Cycle Evidence" in read(
        PLUGIN_ROOT / "skills" / "implementation-evidence" / "SKILL.md"
    )


def test_comment_writing_skill_defines_comment_workflow() -> None:
    text = read(PLUGIN_ROOT / "skills" / "comment-writing" / "SKILL.md")

    assert "Purpose" in text
    assert "When to use" in text
    assert "Inputs to inspect" in text
    assert "Workflow" in text
    assert "Documentation target decision matrix" in text
    assert "Stack-specific comment formats" in text
    assert "Comment quality rules" in text
    assert "Review handoff" in text
    assert "Output" in text
    assert "Do not" in text
    assert "public/exported" in text
    assert "Explain why, not just what." in text
    assert "Do not repeat" in text
    assert "Javadoc" in text
    assert "KDoc" in text
    assert "JSDoc" in text
    assert "docstring" in text
    assert "rustdoc" in text
    assert "docs-researcher handoff" in text
    assert "code-reviewer handoff" in text
    assert "clearer code before comments" in text


def test_comment_specs_reference_documents_required_stacks() -> None:
    text = read(PLUGIN_ROOT / "references" / "comment-specs-by-stack.md")
    first_heading = next(line for line in text.splitlines() if line.startswith("# "))

    assert first_heading == "# Comment Specs by Stack"
    assert "## Code clarity before comments" in text
    assert "## Stack-specific formats" in text
    assert "## Review questions" in text
    assert "| Stack | Preferred format | Applies to | Notes | Official source |" in text
    assert "Code clarity before comments" in text
    assert "Javadoc" in text
    assert "KDoc" in text
    assert "JSDoc" in text
    assert "TSDoc" in text
    assert "docstring" in text
    assert "PEP 257" in text
    assert "Go doc comments" in text
    assert "rustdoc" in text
    assert "XML documentation comments" in text
    assert "PHPDoc" in text
    assert "RDoc" in text
    assert "YARD" in text
    assert "Swift" in text
    assert "Objective-C" in text
    assert "Doxygen" in text
    assert "COMMENT ON" in text
    assert "Shell" in text
    assert "Terraform" in text
    assert "Dockerfile" in text
    assert "Kubernetes" in text
    assert "OpenAPI" in text
    assert "GraphQL" in text
    assert "Proto" in text
    assert "official source" in text
    assert "unrelated refactoring" in text


def test_testing_patterns_reference_documents_required_types() -> None:
    text = read(PLUGIN_ROOT / "references" / "testing-patterns.md")
    test_types = (
        "Unit",
        "Integration",
        "Contract",
        "Component",
        "End-to-end",
        "Smoke",
        "Regression",
        "Characterization",
        "Property-based",
        "Snapshot/Golden",
        "Performance/Benchmark",
        "Security",
        "Accessibility",
        "Migration/Schema",
        "Infrastructure/IaC validation",
    )
    required_labels = (
        "- **When to use:**",
        "- **What to verify:**",
        "- **What to avoid:**",
        "- **Test code structure:**",
        "- **Assertion standard:**",
        "- **Fixture, mock, stub, fake use:**",
        "- **Flaky test prevention:**",
        "- **TDD first failing test:**",
        "- **Use existing project tools first:**",
    )

    assert "# Testing Patterns" in text
    assert "test-assertion-quality.md" in text
    assert "language-test-smells.md" in text
    assert "downstream application project" in text
    assert "observable behavior" in text
    assert "explicit artifact contract" in text
    for smell_phrase in (
        "weak assertions",
        "mock-only assertions",
        "private behavior tests",
        "implementation-detail assertions",
        "broad snapshots",
        "non-diagnostic failures",
        "wrong-layer tests",
        "flaky shared",
        "coverage theater",
    ):
        assert smell_phrase in text
    double_priority = section_body(text, "Test double priority")
    assert "inline minimal arrange" in double_priority
    assert "real domain objects" in double_priority
    assert "repeated arrange becomes clearer with a name" in double_priority
    assert "unused setup does not hide test intent" in double_priority
    assert "Use a mock only when the outbound interaction contract itself is the requirement" in double_priority

    lines = text.splitlines()
    previous_heading_index = -1
    for test_type in test_types:
        heading_index = lines.index(f"## {test_type}")
        assert heading_index > previous_heading_index
        previous_heading_index = heading_index

        section = section_body(text, test_type)

        previous_position = -1
        for label in required_labels:
            position = section.find(label)
            assert position > previous_position
            next_positions = [
                section.find(next_label, position + len(label))
                for next_label in required_labels
                if section.find(next_label, position + len(label)) != -1
            ]
            end_position = min(next_positions) if next_positions else len(section)
            assert section[position + len(label) : end_position].strip()
            previous_position = position

    assert "When to use" in text
    assert "What to verify" in text
    assert "What to avoid" in text
    assert "TDD first failing test" in text


def test_readme_documents_plugin_only_installation() -> None:
    readme = read(PLUGIN_ROOT / "README.md")

    assert "Plugin-only distribution" in readme
    assert "$shared-skills:" in readme
    assert "- `tdd-cycle`:" in readme
    assert "- `comment-writing`:" in readme
    assert "does not copy skills into" in readme
    assert "does not edit AGENTS.md" in readme


def test_claude_readme_uses_harness_neutral_plugin_guidance() -> None:
    readme = read(CLAUDE_PLUGIN_ROOT / "README.md")

    assert ".codex-plugin/plugin.json" not in readme
    assert "restart Codex" not in readme
    assert "generated Codex and Claude plugin manifests" in readme
    assert "restart the host coding agent or tool" in readme


def test_implementation_discipline_prefers_clear_code_before_comments() -> None:
    text = read(PLUGIN_ROOT / "skills" / "implementation-discipline" / "SKILL.md")

    assert "Before explaining unclear code with comments" in text
    assert "better names" in text
    assert "named constants" in text
    assert "extracted expressions/functions" in text
    assert "typed options" in text
    assert "approved scope" in text
    assert "Do not turn readability cleanup into unrelated refactoring" in text


def test_no_scaffold_or_copy_install_flow_exists() -> None:
    assert not (PLUGIN_ROOT / "skills" / "scaffold").exists()
    assert not (PLUGIN_ROOT / "scripts").exists()

    combined = "\n".join(
        read(path)
        for path in sorted(PLUGIN_ROOT.rglob("*"))
        if path.is_file() and path.suffix in {".md", ".json"}
    )

    assert "--install --backup" not in combined
    assert "$CODEX_HOME/skills" not in combined
    assert "~/.codex/skills" not in combined
