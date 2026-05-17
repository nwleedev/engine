<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/references/workflow-artifacts.md -->

# Workflow Artifacts

Use these schemas to keep requirements, specs, plans, implementation evidence, and verification gates traceable across development and non-development work.

## Requirement Packet

| requirement_id | status | requirement | source_text | acceptance_criteria | non_goal | assumption_or_question |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | confirmed |  |  | AC-001:  |  |  |

## Spec Contract

| spec_id | linked_requirement_ids | behavior | interfaces_or_artifacts | failure_modes | compatibility_constraints |
| --- | --- | --- | --- | --- | --- |
| SPEC-001 | REQ-001 |  |  |  |  |

## Spec Ledger

Use a `Spec Ledger` when broad spec IDs are not enough to prove that every
requirement, constraint, edge case, and non-goal was carried into the plan.
Each row must be safe to cite from a plan, test contract, implementation
evidence packet, or completion review.

| spec_clause_id | linked_requirement_ids | source_location | clause_type | validation_intent | priority | confidentiality | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-001.CLAUSE-001 | REQ-001 | spec.md#section | behavior |  | must | public | open |  |

## Plan Contract

| task_id | linked_requirement_ids | linked_spec_clause_ids | steps | target_files_or_artifacts | validation_method | done_criteria | fallback | risk_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | REQ-001 | SPEC-001.CLAUSE-001 |  |  |  |  |  | medium |

## Spec-to-Plan Coverage Matrix

Use a `Spec-to-Plan Coverage Matrix` before implementation and before any
completion claim. `coverage_status` must be one of `covered`,
`missing_plan`, `missing_validation`, `missing_evidence`,
`stale_evidence`, `unresolved_risk`, `deferred_with_owner`, or
`not_applicable_with_reason`.

Use `orphan_task` when a plan task has no requirement link, `needs_spec_mapping`
when it has no spec clause link, `missing_fallback` when expected failure paths
are not named, and `not_run_hidden` when not-run checks are omitted from the
Verification Gate.

| spec_clause_id | linked_requirement_ids | plan_task_ids | scenario_ids | test_or_check_ids | evidence_ids | coverage_status | gap_or_risk | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-001.CLAUSE-001 | REQ-001 | TASK-001 | SCN-001 | TEST-001 | EVID-001 | missing_evidence |  |  |

## Coverage Report

Use a `Coverage Report` as the handoff artifact for completion reviews. It may
refer to a committed JSON report, an ignored local JSON report, or a redacted
Markdown summary when the source spec is confidential. The report must include
the validator command, validator exit code, report path, and any blocking
coverage or fixture governance codes.

| coverage_report_id | matrix_id | validator_command | validator_exit_code | report_path | redacted_markdown_path | blocking_codes | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| COVERAGE-001 | MATRIX-001 |  | 1 |  |  | missing_evidence | blocked |

## Traceability Matrix

| requirement_id | spec_id | spec_clause_id | task_id | evidence_id | changed_files | test_or_check_ids | review_finding_ids | closure_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | SPEC-001 | SPEC-001.CLAUSE-001 | TASK-001 | EVID-001 |  |  |  | pending |  |

## Implementation Evidence

| evidence_id | linked_requirement_ids | linked_spec_clause_ids | linked_task_ids | files_changed | behavior_changed | commands_run | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EVID-001 | REQ-001 | SPEC-001.CLAUSE-001 | TASK-001 |  |  |  |  |

## Verification Gate

| completion_claim | coverage_report_ids | required_evidence_ids | failed_items | not_run_items | residual_risks | final_status |
| --- | --- | --- | --- | --- | --- | --- |
|  | COVERAGE-001 | EVID-001 |  |  |  |  |
