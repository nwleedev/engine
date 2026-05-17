---
name: implementation-evidence
description: Use when recording what changed, why it changed, and which commands or inspections prove the linked requirements and tasks.
metadata:
  short-description: Record traceable implementation evidence
---

# Implementation Evidence

## Purpose

Create an `Implementation Evidence` packet that links requirements, spec clauses, and tasks to changed files, behavior changes, commands run, and remaining evidence gaps.

## Workflow

1. Assign stable evidence IDs using `EVID-001`, `EVID-002`, and increasing numbers.
2. Link each evidence item to requirement IDs, `linked_spec_clause_ids`, and task IDs.
3. List the files, generated artifacts, documents, or operational assets changed.
4. Describe behavior changed in terms of observable outcomes.
5. Record every command run, exit status, and the relevant observed result.
6. Separate failed commands, skipped commands, and not-applicable checks.
7. Route completion claims to `verification-gate` after required evidence is present.

## Development work

- Include test, lint, build, generation, validation, and focused reproduction commands.
- Record generated artifact updates separately from canonical source edits.
- Preserve the difference between a failing RED command and a passing GREEN command when TDD is used.
- Record Fixture Governance Contract evidence when fixtures, mocks, fakes, stubs, snapshots, or generated inputs were added or expanded.

## Non-development work

- Include reviewed source IDs, source conflicts, artifact diffs, review notes, and accepted assumptions.
- Record manual inspection evidence with enough detail for another reviewer to repeat it.
- Keep unverified claims in residual risks instead of evidence.

## Output

```markdown
## Implementation Evidence

| evidence_id | linked_requirement_ids | linked_spec_clause_ids | linked_task_ids | files_changed | behavior_changed | commands_run | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EVID-001 | REQ-001 | SPEC-001.CLAUSE-001 | TASK-001 |  |  |  |  |
```

## Do not

- Do not claim behavior changed without naming observable evidence.
- Do not collapse failed, skipped, and passing commands into one summary.
- Do not omit generated files when generation is part of the acceptance criteria.
- Do not use evidence IDs for work that has not been performed.
- Do not mark fixture-heavy tests as evidence without their fixture governance and real-boundary rationale.
