from __future__ import annotations

from pathlib import Path


FORBIDDEN_LEGACY_NAMES = (
    "requirements-clarifier",
    "research-crosscheck",
    "task-planner",
    "review-checklist",
    "verification-evidence",
    "online-researcher",
    "spec-reviewer",
)

REQUIRED_SHARED_SKILL_REFERENCES = (
    "workflow-artifacts.md",
    "deep-research-pipeline.md",
    "downstream-test-contracts.md",
)

REQUIRED_SHARED_SUBAGENTS = (
    "requirements-reviewer",
    "plan-reviewer",
    "spec-coverage-reviewer",
    "citation-verifier",
    "test-adequacy-reviewer",
    "closure-reviewer",
    "completion-claim-reviewer",
    "risk-reviewer",
)

REQUIRED_WORKFLOW_ARTIFACT_TERMS = (
    "Requirement Packet",
    "requirement_id",
    "Spec Contract",
    "spec_id",
    "Spec Ledger",
    "spec_clause_id",
    "source_location",
    "validation_intent",
    "Plan Contract",
    "linked_spec_clause_ids",
    "steps",
    "done_criteria",
    "fallback",
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
    "review_finding_ids",
    "closure_status",
    "Implementation Evidence",
    "Verification Gate",
)

REQUIRED_DEEP_RESEARCH_TERMS = (
    "Source Ledger",
    "title",
    "url_or_path",
    "publisher",
    "published_or_accessed_date",
    "used_for_claim_ids",
    "Claim Evidence Map",
    "Counterevidence Review",
)

REQUIRED_DOWNSTREAM_TEST_TERMS = (
    "Scenario Test Contract",
    "Acceptance Criteria ID",
    "User Scenario ID",
    "Fixture/Mock Justification",
    "Fixture Governance Contract",
    "fixture_id",
    "real_boundary_preferred",
    "drift_check",
    "unjustified_fixture",
    "fixture_overgrowth",
    "unapproved_mock",
    "missing_real_boundary_check",
    "test_only_behavior",
    "Do not assert only mock calls",
)

SHARED_SKILL_ROOTS = (
    ("codex", Path("plugins/codex/shared-skills")),
    ("claude", Path("plugins/claude/shared-skills")),
)

SHARED_SUBAGENT_ROOTS = (
    ("codex", Path("plugins/codex/shared-subagents"), ".toml"),
    ("claude", Path("plugins/claude/shared-subagents"), ".md"),
)


def validate_workflow_plugins(root: Path) -> list[str]:
    """Validate required workflow plugin artifacts by generated path structure."""

    errors: list[str] = []
    errors.extend(_validate_no_legacy_artifacts(root))
    errors.extend(_validate_required_shared_skill_references(root))
    errors.extend(_validate_shared_skill_schema_terms(root))
    errors.extend(_validate_required_shared_subagents(root))
    return errors


def _validate_no_legacy_artifacts(root: Path) -> list[str]:
    errors: list[str] = []

    for _, relative_root in SHARED_SKILL_ROOTS:
        for legacy_name in FORBIDDEN_LEGACY_NAMES:
            path = root / relative_root / "skills" / legacy_name / "SKILL.md"
            if path.exists():
                errors.append(
                    "legacy generated artifact found: "
                    f"{path.relative_to(root).as_posix()} contains {legacy_name}"
                )

    for _, relative_root, suffix in SHARED_SUBAGENT_ROOTS:
        for legacy_name in FORBIDDEN_LEGACY_NAMES:
            path = root / relative_root / "agents" / f"{legacy_name}{suffix}"
            if path.exists():
                errors.append(
                    "legacy generated artifact found: "
                    f"{path.relative_to(root).as_posix()} contains {legacy_name}"
                )

    return errors


def _validate_required_shared_skill_references(root: Path) -> list[str]:
    errors: list[str] = []

    for harness, relative_root in SHARED_SKILL_ROOTS:
        references_root = root / relative_root / "references"
        for reference in REQUIRED_SHARED_SKILL_REFERENCES:
            path = references_root / reference
            if not path.is_file():
                errors.append(
                    "missing required shared-skills reference "
                    f"for {harness}: {path.relative_to(root).as_posix()}"
                )

    return errors


def _validate_shared_skill_schema_terms(root: Path) -> list[str]:
    errors: list[str] = []
    required_terms_by_reference = {
        "workflow-artifacts.md": REQUIRED_WORKFLOW_ARTIFACT_TERMS,
        "deep-research-pipeline.md": REQUIRED_DEEP_RESEARCH_TERMS,
        "downstream-test-contracts.md": REQUIRED_DOWNSTREAM_TEST_TERMS,
    }

    for harness, relative_root in SHARED_SKILL_ROOTS:
        references_root = root / relative_root / "references"
        for reference, required_terms in required_terms_by_reference.items():
            path = references_root / reference
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for term in required_terms:
                if term not in text:
                    errors.append(
                        "missing shared-skills schema term "
                        f"for {harness}: {path.relative_to(root).as_posix()} "
                        f"must include {term}"
                    )

    return errors


def _validate_required_shared_subagents(root: Path) -> list[str]:
    errors: list[str] = []

    for harness, relative_root, suffix in SHARED_SUBAGENT_ROOTS:
        agents_root = root / relative_root / "agents"
        for agent in REQUIRED_SHARED_SUBAGENTS:
            path = agents_root / f"{agent}{suffix}"
            if not path.is_file():
                errors.append(
                    "missing required shared-subagents agent "
                    f"for {harness}: {path.relative_to(root).as_posix()}"
                )

    return errors
