---
name: spec-contract
description: Use when confirmed requirements need a behavior contract before implementation planning, test design, or review.
metadata:
  short-description: Convert requirements into a spec contract
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/spec-contract/SKILL.md -->


# Spec Contract

## Purpose

Create a `Spec Contract` that defines intended behavior, interfaces or artifacts, failure modes, and compatibility constraints before planning implementation or downstream tests. When the spec has multiple clauses or confidential source text, also prepare a `Spec Ledger` so later plans can cite stable `spec_clause_id` values without exposing sensitive text.

Use `../../references/workflow-artifacts.md` when table schemas, row-level rules, or coverage status values are needed.

## Workflow

1. Start from a `Requirement Packet` and copy only confirmed requirement IDs.
2. Assign stable spec IDs using `SPEC-001`, `SPEC-002`, and increasing numbers.
3. Describe externally observable behavior rather than implementation details.
4. Name every interface, file artifact, command, schema, UI state, or operational artifact affected by the behavior.
5. Include expected failure modes, degraded states, rollback expectations, and compatibility constraints.
6. Split behavior, artifact, failure-mode, compatibility, non-goal, and validation requirements into `Spec Ledger` rows when a plan must prove complete coverage.
7. Mark unresolved or inferred behavior as a question instead of silently deciding it.
8. Route executable work to `plan-contract`, test design to `scenario-test-designer`, and clause coverage checks to `spec-plan-coverage`.

## Development work

- Tie public APIs, generated artifacts, configuration, data shapes, and commands to requirement IDs.
- Record compatibility constraints for existing callers, generated plugin outputs, and test fixtures.
- Keep failure modes concrete enough to drive negative or regression tests.
- Use `source_location` and `validation_intent` in the Spec Ledger when the source spec cannot be committed.

## Non-development work

- Treat documents, research packets, review outputs, and decision records as artifacts with observable acceptance criteria.
- Record audience, format, source authority, and update constraints when they affect the spec.
- Keep unsupported claims out of the spec until `claim-evidence-map` can support them.

## Output

```markdown
## Spec Contract

| spec_id | linked_requirement_ids | behavior | interfaces_or_artifacts | failure_modes | compatibility_constraints |
| --- | --- | --- | --- | --- | --- |
| SPEC-001 | REQ-001 |  |  |  |  |

## Spec Ledger

| spec_clause_id | linked_requirement_ids | source_location | clause_type | validation_intent | priority | confidentiality | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-001.CLAUSE-001 | REQ-001 | spec.md#section | behavior | automated test | must | public | open |  |
```

## Do not

- Do not create a spec without linked requirement IDs.
- Do not hide unresolved behavior inside vague language.
- Do not describe private implementation choices as user-facing behavior.
- Do not omit compatibility constraints when existing artifacts or users are affected.
- Do not rely only on broad spec IDs when later plan coverage needs clause-level proof.
