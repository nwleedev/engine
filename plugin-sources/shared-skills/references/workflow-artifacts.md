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

## Plan Contract

| task_id | linked_requirement_ids | steps | target_files_or_artifacts | validation_method | done_criteria | fallback | risk_level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | REQ-001 |  |  |  |  |  | medium |

## Traceability Matrix

| requirement_id | spec_id | task_id | evidence_id | changed_files | test_or_check_ids | review_finding_ids | closure_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | SPEC-001 | TASK-001 | EVID-001 |  |  |  | pending |  |

## Implementation Evidence

| evidence_id | linked_requirement_ids | linked_task_ids | files_changed | behavior_changed | commands_run | result |
| --- | --- | --- | --- | --- | --- | --- |
| EVID-001 | REQ-001 | TASK-001 |  |  |  |  |

## Verification Gate

| completion_claim | required_evidence_ids | failed_items | not_run_items | residual_risks | final_status |
| --- | --- | --- | --- | --- | --- |
|  | EVID-001 |  |  |  |  |
