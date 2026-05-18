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

## Scenario Change Map

Use this contract when existing scenarios, tests, artifacts, or acceptance
criteria may be affected by current requirements. Each row must connect one
previous scenario or test to the current acceptance criteria before new or
replacement test contracts are created.

| scenario_change_id | previous_scenario_or_test_id | linked_scenario_ids | current_acceptance_criteria_id | relationship_to_current_requirement | required_action | replacement_or_gap_id | reconciliation_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SCM-001 | TEST-001 | SCN-001 | AC-001 | still_valid | keep |  | REC-001 |

Allowed `relationship_to_current_requirement` values are `still_valid`,
`partially_valid`, `obsolete`, `contradicts_current_requirement`,
`missing_current_coverage`, and `not_applicable_with_reason`. Use
`still_valid` only when the previous scenario or test proves the current
acceptance criterion without assertion, fixture, or artifact drift. Use
`partially_valid` when it still proves part of the current behavior but needs
new coverage for a named gap. Use `obsolete` or
`contradicts_current_requirement` when the previous evidence must not count as
core coverage for the current requirement.

Allowed `required_action` values are `keep`, `update`, `split`, `replace`,
`demote`, `delete`, `quarantine`, `add_new_coverage`, and
`manual_or_inspection_evidence`. Use `keep` only with `still_valid`; use
`add_new_coverage` when no previous scenario or test proves the current
acceptance criterion. `replacement_or_gap_id` must name the replacement test,
coverage gap, residual risk, or manual evidence row when `required_action` is
not `keep`.

## Current Requirement Coverage Contract

Use this contract to decide what currently counts as core coverage after a
requirement, acceptance criterion, or test suite has changed. Every row must
join to one or more scenario IDs through `linked_scenario_ids`, and
reconciliation-required work must join to the relevant `reconciliation_id`.

| coverage_contract_id | reconciliation_id | current_requirement_id | acceptance_criteria_id | linked_scenario_ids | coverage_status | core_evidence | residual_gap | residual_risk_id | manual_or_inspection_evidence | replacement_coverage | owner_or_followup | blocking_risks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CRC-001 | REC-001 | REQ-001 | AC-001 | SCN-001 | covered | TEST-001 | none |  |  |  |  | none |

Allowed `coverage_status` values are `covered`, `covered_with_manual_evidence`,
`partial_gap`, `replacement_required`, `blocked_by_risk`, and
`not_applicable_with_reason`. Use `covered` only when executable, current,
non-quarantined evidence proves every linked scenario. Use
`covered_with_manual_evidence` only when automated coverage is infeasible and
`manual_or_inspection_evidence` names a repeatable check. Use `partial_gap` or
`replacement_required` when `replacement_coverage` or `residual_gap` is needed
before the requirement can be completed.

`replacement_coverage` must name the new or retained evidence that replaces a
demoted, obsolete, contradictory, or quarantined test. `blocking_risks` must be
`none` or a comma-separated list of blocking risk codes such as
`stale_test_counted_as_core`, `test_artifact_drift_unresolved`,
`unjustified_fixture`, `missing_real_boundary_check`, `test_only_behavior`,
`missing_current_coverage`, or `manual_evidence_not_repeatable`.
`owner_or_followup` is required when `coverage_status` is not `covered`.

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

## TDD Cycle Evidence

Use this contract when a test is written or modified through a TDD cycle. A row
must join to the scenario and acceptance criterion it proves. When
reconciliation was required, it must also join to the same `reconciliation_id`
used by the Scenario Change Map and Current Requirement Coverage Contract.

| tdd_evidence_id | scenario_id | acceptance_criteria_id | reconciliation_id | test_file | failing_command | observed_failure | passing_command | observed_result | residual_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TDD-001 | SCN-001 | AC-001 | REC-001 |  |  |  |  |  | none |

`failing_command` and `observed_failure` are required for new behavior or bug
fix coverage unless the row records approved characterization-only evidence.
`passing_command` and `observed_result` are required before TDD evidence can be
used as completion evidence. `residual_gap` must be `none` or join to a gap,
risk, owner follow-up, manual evidence, or replacement coverage row.

## Join Rules

- `Scenario Test Contract.User Scenario ID`,
  `Scenario Change Map.linked_scenario_ids`,
  `Current Requirement Coverage Contract.linked_scenario_ids`, and
  `TDD Cycle Evidence.scenario_id` must use the same stable `SCN-*` IDs.
- `acceptance_criteria_id` and `current_acceptance_criteria_id` values must
  join to a current Requirement Packet, Spec Contract, or Scenario Test
  Contract acceptance criteria ID.
- `reconciliation_id` must join Scenario Change Map, Current Requirement
  Coverage Contract, TDD Cycle Evidence, Implementation Evidence, and
  Verification Gate rows whenever the selected testing route required
  reconciliation.
- Core completion evidence must not count stale, obsolete, contradictory,
  orphaned, quarantined, or drift-unreviewed tests unless replacement coverage
  or repeatable manual evidence is recorded.

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
