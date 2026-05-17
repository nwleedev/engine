from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path("plugins/codex/shared-skills")
CLAUDE_PLUGIN_ROOT = Path("plugins/claude/shared-skills")
SKILLS = (
    "requirements-packet",
    "spec-contract",
    "plan-contract",
    "implementation-evidence",
    "verification-gate",
    "research-plan",
    "source-ledger",
    "claim-evidence-map",
    "scenario-test-designer",
    "test-plan-contract",
    "tdd-test-writing",
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
    assert manifest["version"] == "0.2.8"
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
        "missing_plan",
        "missing_validation",
        "missing_evidence",
        "stale_evidence",
        "unresolved_risk",
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

    assert (
        "| fixture_id | linked_scenario_ids | linked_spec_clause_ids | fixture_type | real_boundary_preferred | justification | owner | drift_check | expiry_or_update_trigger |"
        in text
    )
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
    assert "missing_real_boundary_check" in text
    assert "test_only_behavior" in text
    assert "Do not assert only mock calls" in text
    assert "Do not create broad fixture factories" in text
    assert "observable behavior" in text


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
    assert "missing_evidence" in text
    assert "stale_evidence" in text
    assert "unresolved_risk" in text
    assert "unjustified_fixture" in text
    assert "fixture_overgrowth" in text
    assert "missing_real_boundary_check" in text
    assert "test_only_behavior" in text


def test_tdd_test_writing_skill_defines_tdd_workflow() -> None:
    text = read(PLUGIN_ROOT / "skills" / "tdd-test-writing" / "SKILL.md")

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


def test_tdd_test_types_reference_documents_required_types() -> None:
    text = read(PLUGIN_ROOT / "references" / "tdd-test-types.md")
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

    assert "# TDD Test Types" in text
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
    assert "- `tdd-test-writing`:" in readme
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
