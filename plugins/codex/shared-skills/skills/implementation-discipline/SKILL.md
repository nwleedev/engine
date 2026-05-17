---
name: implementation-discipline
description: Use when making code, documentation, configuration, or operational changes and needing disciplined execution without subagents.
metadata:
  short-description: Keep main-session changes scoped and traceable
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/implementation-discipline/SKILL.md -->


# Implementation Discipline

Keep main-session changes scoped, traceable, and verifiable.

## Workflow

1. Identify the exact change type: code, documentation, configuration, operation, or mixed.
2. Read the relevant local rules, files, dependencies, and existing patterns before editing.
3. Keep the edit scope tied to the user's approved goal.
4. Record touched areas, validation needs, and review handoff points.
5. For behavior-changing work, route acceptance criteria through `scenario-test-designer`, `test-plan-contract`, and `tdd-test-writing` before completion unless tests are explicitly inapplicable.
6. Use `implementation-evidence` and `verification-gate` before completion claims.

## Development work

- Check likely imports, package usage, tests, lint rules, and compatibility concerns.
- Do not treat necessary tests as optional follow-up when the implementation changes user-visible behavior or public contracts.
- Before explaining unclear code with comments, consider whether better names, named constants, extracted expressions/functions, enums, typed options, or smaller units would make the intent clear within the approved scope.
- Avoid unrelated refactors unless they are required for the approved change.
- Prefer existing project patterns and minimal focused edits.

## Non-development work

- Keep source notes, assumptions, structure, and decision criteria visible.
- Preserve the requested audience, tone, format, and delivery constraints.
- Track changed claims, recommendations, or operational instructions.

## Output

- Change scope
- Files or artifacts touched
- Execution notes
- Validation needs
- Review handoff points

## Do not

- Do not expand the task beyond approved scope.
- Do not introduce new dependencies or tools without approval.
- Do not skip local project rules.
- Do not claim completion without verification evidence.
- Do not turn readability cleanup into unrelated refactoring beyond the approved scope.
