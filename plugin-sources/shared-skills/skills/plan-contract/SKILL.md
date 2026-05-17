---
name: plan-contract
description: Use when a spec or confirmed requirement needs an implementation plan with target artifacts, validation methods, and fallback criteria.
metadata:
  short-description: Build an evidence-ready implementation plan
---

# Plan Contract

## Purpose

Create a `Plan Contract` that turns confirmed requirements or spec contracts into small executable tasks with ordered steps, validation methods, done criteria, fallback paths, and risk levels. When a Spec Ledger exists, every task must carry `linked_spec_clause_ids` so `spec-plan-coverage` can detect omissions before implementation.

Use `../../references/workflow-artifacts.md` when table schemas, row-level rules, or coverage status values are needed.

## Workflow

1. Start from confirmed requirements, spec IDs, and available `spec_clause_id` values; do not plan from unresolved questions.
2. Assign stable task IDs using `TASK-001`, `TASK-002`, and increasing numbers.
3. Keep each task independently verifiable and scoped to named files or artifacts.
4. Define the steps, validation command, review method, or inspection evidence for each task.
5. Define done criteria and a fallback for blocked commands, failing tests, missing context, or incompatible artifacts.
6. Assign a risk level so high-risk work receives stronger test, review, or rollback evidence.
7. Order tasks so contract tests or artifact checks fail before implementation and pass after implementation.
8. Run `spec-plan-coverage` before implementation when the spec has clause-level requirements.
9. Route completed task evidence to `implementation-evidence` and closure checks to `verification-gate`.

## Development work

- Include source files, generated files, tests, build scripts, and validation commands in the target artifact list.
- Prefer the smallest command that proves each task before running broader validation.
- Preserve existing branch and worktree constraints from project instructions.
- Treat a required spec clause without a plan task as `missing_plan`.
- Treat a plan task without a validation method for its linked spec clause as `missing_validation`.

## Non-development work

- Treat documents, research artifacts, and review packets as target artifacts with explicit validation methods.
- Include source-checking, counterevidence review, and stakeholder acceptance where code tests do not apply.
- Record fallback paths for missing sources, stale documents, or incomplete user decisions.

## Output

```markdown
## Plan Contract

| task_id | linked_requirement_ids | linked_spec_clause_ids | steps | target_files_or_artifacts | validation_method | done_criteria | fallback | risk_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | REQ-001 | SPEC-001.CLAUSE-001 |  |  |  |  |  | medium |
```

## Do not

- Do not plan tasks that cannot be validated.
- Do not group unrelated files or behaviors into one task.
- Do not start implementation when blocking assumptions remain unaccepted.
- Do not omit fallback criteria for expected failure points.
- Do not omit `linked_spec_clause_ids` when planning from a Spec Ledger.
