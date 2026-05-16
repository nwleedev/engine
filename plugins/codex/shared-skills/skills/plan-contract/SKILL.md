---
name: plan-contract
description: Use when a spec or confirmed requirement needs an implementation plan with target artifacts, validation methods, and fallback criteria.
metadata:
  short-description: Build an evidence-ready implementation plan
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/plan-contract/SKILL.md -->


# Plan Contract

## Purpose

Create a `Plan Contract` that turns confirmed requirements or spec contracts into small executable tasks with validation methods and failure fallback paths.

## Workflow

1. Start from confirmed requirements or spec IDs; do not plan from unresolved questions.
2. Assign stable task IDs using `TASK-001`, `TASK-002`, and increasing numbers.
3. Keep each task independently verifiable and scoped to named files or artifacts.
4. Define the validation command, review method, or inspection evidence for each task.
5. Define a failure fallback for blocked commands, failing tests, missing context, or incompatible artifacts.
6. Order tasks so contract tests or artifact checks fail before implementation and pass after implementation.
7. Route completed task evidence to `implementation-evidence` and closure checks to `verification-gate`.

## Development work

- Include source files, generated files, tests, build scripts, and validation commands in the target artifact list.
- Prefer the smallest command that proves each task before running broader validation.
- Preserve existing branch and worktree constraints from project instructions.

## Non-development work

- Treat documents, research artifacts, and review packets as target artifacts with explicit validation methods.
- Include source-checking, counterevidence review, and stakeholder acceptance where code tests do not apply.
- Record fallback paths for missing sources, stale documents, or incomplete user decisions.

## Output

```markdown
## Plan Contract

| task_id | linked_requirement_ids | target_files_or_artifacts | validation_method | failure_fallback |
| --- | --- | --- | --- | --- |
| TASK-001 | REQ-001 |  |  |  |
```

## Do not

- Do not plan tasks that cannot be validated.
- Do not group unrelated files or behaviors into one task.
- Do not start implementation when blocking assumptions remain unaccepted.
- Do not omit fallback criteria for expected failure points.
