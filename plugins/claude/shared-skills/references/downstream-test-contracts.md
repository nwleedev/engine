<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/references/downstream-test-contracts.md -->

# Downstream Test Contracts

Use these contracts when shared skills are applied inside a downstream project and tests must prove observable behavior against acceptance criteria.

## Scenario Test Contract

| downstream project | Acceptance Criteria ID | User Scenario ID | test_layer | test_file | test_command | observable behavior |
| --- | --- | --- | --- | --- | --- | --- |
|  | AC-001 | SCN-001 |  |  |  |  |

## Fixture/Mock Justification

| Name | Type | Needed Because | Real Alternative Considered | Behavior Hidden | Decision |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Fixture and Mock Priority

1. Inline minimal arrange in the test body.
2. Real domain object or in-memory implementation.
3. Named fixture when repeated setup is clearer and unused fields are absent.
4. Fake or stub for a stable external boundary.
5. Mock only when the outbound interaction contract itself is the requirement or the dependency is nondeterministic.

## Guardrails

- Do not assert only mock calls when observable behavior can be asserted.
- Do not create broad fixture factories before repeated setup proves a named fixture is clearer.
- Keep every core scenario linked to an Acceptance Criteria ID and User Scenario ID.
- Record the exact failing and passing command for TDD evidence.
