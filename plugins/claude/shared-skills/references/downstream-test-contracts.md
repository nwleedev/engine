<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/references/downstream-test-contracts.md -->

# Downstream Test Contracts

Use these contracts when shared skills are applied inside a downstream project and tests must prove observable behavior against acceptance criteria.

When `testing-workflow` routes to `test-suite-reconciliation`, complete the
`Existing Test Relevance Inventory` and `Test Artifact Drift Inventory` before
creating new downstream contracts. Do not count stale, demoted, deleted, or
quarantined tests as core coverage in the contracts below.

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

When fixture drift can affect completion evidence, include source location and
generation date in the fixture note or evidence bundle. Treat `stale_fixture` as
a failure when fixture source, generation date, drift status, or update trigger
shows the fixture no longer reflects the project boundary it claims to model.

## Artifact Drift Contract

Use this contract for snapshots, goldens, cassettes, generated expected output,
schema example files, benchmark baseline files, and IaC expected output files
that support a downstream test claim. For full classification rules, use
`test-artifact-drift.md`.

| artifact_id | artifact_type | linked_test_ids | expectation_status | drift_status | source_or_generator | owner | review_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ART-001 | schema example | TEST-001 | artifact_expected | reviewed_current |  |  |  |

Allowed `expectation_status` values are `artifact_expected`,
`no_artifact_expected`, `no_existing_artifact_found`, and `blocker_drift`.
Treat `test_artifact_drift_unresolved`, `snapshot_drift_unreviewed`, and
`mock_contract_mismatch` as blocking failures when an artifact-backed test is
used as core evidence.

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
- Treat `unapproved_mock` as a failure when new mocks or mock-call assertions exceed the approved mock budget.
- Treat `stale_fixture` as a failure when fixture drift review shows a stale source, missing update trigger, or mismatch with the current spec/project boundary.
- Treat `missing_real_boundary_check` as a failure when the test relies on doubles without a high-fidelity boundary or documented real-boundary reason.
- Treat `test_only_behavior` as a failure when production behavior is added only to satisfy a test fixture, mock, or fake instead of the user scenario.
- Treat `test_artifact_drift_unresolved` as a failure when snapshot, golden, generated expected output, schema example, benchmark baseline, or IaC expected output drift is unresolved.
- Treat `quarantined_test_counted_as_evidence` as a failure when quarantined tests are included in core completion evidence.
