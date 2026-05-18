---
name: scenario-test-designer
description: Use when acceptance criteria need downstream user scenarios, happy paths, boundary scenarios, and failure scenarios before writing tests.
metadata:
  short-description: Design scenario-based test coverage
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/scenario-test-designer/SKILL.md -->


# Scenario Test Designer

## Purpose

Create a scenario test design that links acceptance criteria to user-visible happy paths, boundary scenarios, failure scenarios, and any previous scenario or test relationship before selecting test files or writing tests.

Use this as a required gate for implementation work that changes observable behavior or acceptance criteria. If the work is test-inapplicable, record the reason and route the residual risk to `verification-gate`.

Use `../../references/downstream-test-contracts.md` when fixture governance,
scenario mapping, canonical Scenario Change Map fields, join rules, allowed
values, or test contract details are needed.

## Workflow

1. Start from acceptance criteria in a `Requirement Packet` or `Spec Contract`.
2. Assign stable user scenario IDs using `SCN-001`, `SCN-002`, and increasing numbers.
3. Link each scenario to an acceptance criteria ID.
4. Define the happy path in observable behavior terms.
5. Define at least one boundary scenario when inputs, state, permissions, size, time, concurrency, or compatibility can vary.
6. Define at least one failure scenario when safe failure, error display, rejection, rollback, or degraded behavior matters.
7. When the work follows a reconciliation route, produce a `Scenario Change Map` that relates previous scenarios or tests to the current acceptance criteria before new test contracts are created; use the canonical allowed values and join rules in `downstream-test-contracts.md`.
8. Route executable test contracts to `test-plan-contract` or concrete test writing to `tdd-cycle`.

## Development work

- Choose scenarios that can fail through public APIs, UI behavior, generated artifacts, or system boundaries.
- Prefer observable behavior over private function calls or incidental implementation details.
- Name external dependencies that may require a fake, stub, or mock justification.

## Non-development work

- Use scenarios to evaluate documentation, runbooks, operational processes, and review checklists when code tests do not apply.
- Keep each scenario linked to one acceptance criterion unless the behavior genuinely spans several criteria.
- Record untestable acceptance criteria as requirement or spec gaps.

## Output

```markdown
## Scenario Test Designer

| user_scenario_id | acceptance_criteria_id | happy_path | boundary_scenario | failure_scenario |
| --- | --- | --- | --- | --- |
| SCN-001 | AC-001 |  |  |  |

## Scenario Change Map

| scenario_id | previous_acceptance_criteria | current_acceptance_criteria | scenario_status | affected_tests | required_action |
| --- | --- | --- | --- | --- | --- |
| SCN-001 | AC-OLD-001 | AC-001 | still_valid | TEST-001 | keep |

## Scenario Change Map Extension

| scenario_id | previous_scenario_or_test_id | relationship_to_current_requirement | replacement_or_gap_id | reconciliation_id |
| --- | --- | --- | --- | --- |
| SCN-001 | TEST-001 | still_valid |  | REC-001 |
```

## Do not

- Do not count scenarios without acceptance criteria as core coverage.
- Do not skip the `Scenario Change Map` when existing scenario or test evidence may be affected by current acceptance criteria.
- Do not design tests around mocks when user-visible behavior can be asserted.
- Do not omit failure scenarios for risky or externally visible behavior.
- Do not merge unrelated user journeys into one scenario.
