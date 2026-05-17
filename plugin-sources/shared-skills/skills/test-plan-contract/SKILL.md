---
name: test-plan-contract
description: Use when user scenarios need concrete test layers, files, commands, fixture or mock policy, and evidence IDs before implementation or TDD.
metadata:
  short-description: Turn scenarios into executable test contracts
---

# Test Plan Contract

## Purpose

Create a `Test Plan Contract` that maps each scenario to the test layer, test file, test command, fixture or mock policy, and evidence ID required for completion.

For implementation work that changes observable behavior, this contract is required before claiming completion. It may state that automated tests are not feasible, but it must then name the repeatable manual or inspection evidence and residual risk.

## Workflow

1. Start from scenario IDs and acceptance criteria IDs produced by `scenario-test-designer`.
2. Select the narrowest existing test layer that can fail for the observable behavior.
3. Name the test file or generated artifact that should carry the test.
4. Name the exact command that proves failure and pass status.
5. State the fixture and mock policy, including why real objects or in-memory substitutes are not enough when doubles are used.
6. Assign an evidence ID that will be filled by `implementation-evidence`.
7. Route test implementation to `tdd-test-writing`.

## Development work

- Prefer existing test frameworks, directories, helpers, and command conventions.
- Keep fixtures minimal and named only when repeated setup is clearer.
- Use mocks only when the outbound interaction contract is the requirement or the dependency is nondeterministic.

## Non-development work

- Use this contract for examples, validation scripts, document checks, or manual test protocols when automated tests are not feasible.
- Record manual validation as evidence only when the command or inspection method is repeatable.
- Route unsupported coverage claims to `verification-gate` as residual risk.

## Output

```markdown
## Test Plan Contract

| scenario_id | acceptance_criteria_id | test_layer | test_file | test_command | fixture_mock_policy | evidence_id |
| --- | --- | --- | --- | --- | --- | --- |
| SCN-001 | AC-001 |  |  |  |  | EVID-001 |
```

## Do not

- Do not choose a broader test layer when a narrower public-boundary test can prove the behavior.
- Do not create broad fixture factories before repeated setup proves the need.
- Do not use mocks where observable behavior can be asserted directly.
- Do not omit exact test commands from completion evidence.
