---
name: test-plan-contract
description: Use when user scenarios need concrete test layers, files, commands, fixture or mock policy, and evidence IDs before implementation or TDD.
metadata:
  short-description: Turn scenarios into executable test contracts
---

# Test Plan Contract

## Purpose

Create a `Test Plan Contract` that maps each scenario to the test layer, test file, test command, fixture or mock policy, Fixture Governance Contract, current requirement coverage, and evidence ID required for completion.

For implementation work that changes observable behavior, this contract is required before claiming completion. It may state that automated tests are not feasible, but it must then name the repeatable manual or inspection evidence and residual risk.

Use `../../references/downstream-test-contracts.md` when fixture governance,
scenario mapping, canonical Current Requirement Coverage Contract fields, join
rules, allowed values, or test contract details are needed.

## Workflow

1. Start from scenario IDs and acceptance criteria IDs produced by `scenario-test-designer`.
2. Select the narrowest existing test layer that can fail for the observable behavior.
3. Name the test file or generated artifact that should carry the test.
4. Name the exact command that proves failure and pass status.
5. State the fixture and mock policy, including why real objects, high-fidelity boundaries, or in-memory substitutes are not enough when doubles are used.
6. Set the fixture budget. Default to `0`; any fixture, mock, fake, stub, snapshot, seed, or generated input must have a Fixture Governance Contract row.
7. Assign an evidence ID that will be filled by `implementation-evidence`.
8. When reconciliation was required, link the current coverage row to the `reconciliation_id` and `linked_scenario_ids`, then record replacement coverage or residual risk before routing new tests.
9. Produce a `Current Requirement Coverage Contract` that separates current core evidence from residual gaps, manual or inspection evidence, replacement coverage, and owner follow-up; use the canonical allowed values and join rules in `downstream-test-contracts.md`.
10. Route test implementation to `tdd-cycle`.

## Development work

- Prefer existing test frameworks, directories, helpers, and command conventions.
- Keep fixtures minimal and named only when repeated setup is clearer.
- Use mocks only when the outbound interaction contract is the requirement or the dependency is nondeterministic.
- Fail the plan for `unjustified_fixture`, `fixture_overgrowth`, `missing_real_boundary_check`, or `test_only_behavior` when fixture governance is incomplete.

## Non-development work

- Use this contract for examples, validation scripts, document checks, or manual test protocols when automated tests are not feasible.
- Record manual validation as evidence only when the command or inspection method is repeatable.
- Route unsupported coverage claims to `verification-gate` as residual risk.

## Output

```markdown
## Test Plan Contract

| scenario_id | acceptance_criteria_id | linked_spec_clause_ids | test_layer | test_file | test_command | fixture_mock_policy | fixture_governance_ids | evidence_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCN-001 | AC-001 | SPEC-001.CLAUSE-001 |  |  |  |  | FX-001 | EVID-001 |

## Fixture Governance Contract

| fixture_id | linked_scenario_ids | linked_spec_clause_ids | fixture_type | real_boundary_preferred | justification | owner | drift_check | expiry_or_update_trigger |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FX-001 | SCN-001 | SPEC-001.CLAUSE-001 | fixture | yes |  |  |  |  |

## Current Requirement Coverage Contract

| coverage_contract_id | reconciliation_id | current_requirement_id | acceptance_criteria_id | linked_scenario_ids | coverage_status | core_evidence | residual_gap | residual_risk_id | manual_or_inspection_evidence | replacement_coverage | owner_or_followup | blocking_risks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CRC-001 | REC-001 | REQ-001 | AC-001 | SCN-001 | covered | TEST-001 | none |  |  |  |  | none |
```

## Do not

- Do not choose a broader test layer when a narrower public-boundary test can prove the behavior.
- Do not route reconciliation-required work to `tdd-cycle` without a current coverage row that links accepted evidence, gaps, or residual risk to the `reconciliation_id`.
- Do not create broad fixture factories before repeated setup proves the need.
- Do not use mocks where observable behavior can be asserted directly.
- Do not omit exact test commands from completion evidence.
- Do not increase fixtures, mocks, fakes, stubs, snapshots, or generated inputs without fixture governance.
