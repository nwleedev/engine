---
name: requirements-packet
description: Use when a user request must be converted into confirmed requirements, inferred assumptions, open questions, non-goals, and acceptance criteria before planning or implementation.
metadata:
  short-description: Build a traceable requirement packet
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/requirements-packet/SKILL.md -->


# Requirements Packet

## Purpose

Create a `Requirement Packet` before planning, implementation, review, research, or test writing when the user's request has more than one requirement, any ambiguity, or any completion claim risk.

Use `../../references/workflow-artifacts.md` when table schemas, row-level rules, or coverage status values are needed.

## Workflow

1. Quote or paraphrase the relevant user source text for each requirement.
2. Assign stable IDs using `REQ-001`, `REQ-002`, and increasing numbers.
3. Mark each requirement as `confirmed`, `inferred`, `open`, or `rejected`.
4. Separate non-goals from requirements.
5. Write acceptance criteria as observable outcomes.
6. Ask only blocking questions that prevent a defensible plan.
7. Route implementation work to `plan-contract` only after confirmed requirements are sufficient.

## Development work

- Capture behavior, target files or interfaces, validation expectations, and constraints before writing code.
- Treat inferred technical assumptions as unconfirmed until the user accepts them or local evidence proves them.
- Route test-writing requirements to `scenario-test-designer`, `test-plan-contract`, or `tdd-test-writing` after acceptance criteria are stable.

## Non-development work

- Capture audience, format, source, decision, and delivery constraints as first-class requirements.
- Separate research questions, planning requests, review-only requests, and completion claims before routing.
- Keep open questions small and blocking; do not ask questions that can be answered from provided context.

## Output

```markdown
## Requirement Packet

| requirement_id | status | requirement | source_text | acceptance_criteria | non_goal | assumption_or_question |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | confirmed |  |  |  |  |  |
```

## Do not

- Do not merge multiple requirements into one ID.
- Do not treat inferred assumptions as confirmed requirements.
- Do not plan implementation until blocking questions are resolved or explicitly accepted as assumptions.
- Do not omit non-goals when the user names scope boundaries.
