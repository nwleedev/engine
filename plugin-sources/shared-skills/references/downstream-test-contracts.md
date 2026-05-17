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

## Fixture Governance Contract

Use a `Fixture Governance Contract` whenever a fixture, mock, fake, stub,
snapshot, seed record, generated input, or test-only adapter is added or
expanded. The default fixture budget is `0`; every exception must be tied to
observable behavior, a real-boundary alternative, and a drift check.

| fixture_id | linked_scenario_ids | linked_spec_clause_ids | fixture_type | real_boundary_preferred | justification | owner | drift_check | expiry_or_update_trigger |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FX-001 | SCN-001 | SPEC-001.CLAUSE-001 | fixture | yes |  |  |  |  |

## Fixture and Mock Priority

1. Inline minimal arrange in the test body.
2. Real domain object or in-memory implementation.
3. High-fidelity boundary such as a local API handler, repository, parser, CLI, component render, or database transaction when it is fast and deterministic.
4. Named fixture when repeated setup is clearer and unused fields are absent.
5. Fake or stub for a stable external boundary.
6. Mock only when the outbound interaction contract itself is the requirement or the dependency is nondeterministic.

## Guardrails

- Do not assert only mock calls when observable behavior can be asserted.
- Do not create broad fixture factories before repeated setup proves a named fixture is clearer.
- Keep every core scenario linked to an Acceptance Criteria ID and User Scenario ID.
- Record the exact failing and passing command for TDD evidence.
- Treat `unjustified_fixture` as a failure when a fixture lacks a linked scenario, linked spec clause, or real-boundary alternative.
- Treat `fixture_overgrowth` as a failure when fixture count, factory fields, snapshot size, or generated inputs grow beyond the approved fixture budget.
- Treat `missing_real_boundary_check` as a failure when the test relies on doubles without a high-fidelity boundary or documented real-boundary reason.
- Treat `test_only_behavior` as a failure when production behavior is added only to satisfy a test fixture, mock, or fake instead of the user scenario.
