---
name: test-suite-reconciliation
description: Use when existing requirements, public contracts, expected artifacts, or test artifacts may have changed and the test suite must be reconciled before new tests are added or evidence is accepted.
metadata:
  short-description: Reconcile existing tests and test artifacts against changed requirements.
---

# Test Suite Reconciliation

## Purpose

Use this skill before adding or accepting tests when a requirement, public API,
schema, migration, bug expectation, security policy, performance budget,
generated artifact contract, or expected artifact baseline may have changed.

The goal is to identify existing tests and artifacts that are still valid,
must be updated, should be split or moved, must be demoted or deleted, or need
temporary quarantine. Reconciliation prevents stale or contradictory tests from
being counted as core coverage and produces a `Reconciliation Contract` that
can safely feed `test-plan-contract` and `tdd-cycle`.

Use `../../references/test-relevance-decisions.md`,
`../../references/test-artifact-drift.md`,
`../../references/downstream-test-contracts.md`, and
`../../references/testing-patterns.md` when classifying test relevance,
artifact drift, fixture governance, and the next test pattern.
Use `../../references/downstream-test-contracts.md` when fixture governance, scenario mapping, or test contract details are needed.

## Workflow

1. **Requirement Change Detection**: Identify the changed requirement,
   acceptance criteria, public contract, bug expectation, artifact baseline,
   or compatibility promise. Record the previous expectation and the new
   expectation before touching test code or snapshots.
2. **Affected Test and Artifact Discovery**: Search for tests, fixtures,
   mocks, fakes, stubs, snapshots, goldens, seeds, cassettes, generated
   expected outputs, schema examples, benchmark baselines, and IaC expected
   outputs that claim coverage for the changed expectation.
3. **Existing Test Relevance Classification**: Classify each affected test
   with exactly one decision: `keep`, `update`, `split`, `move`, `demote`,
   `delete`, or `quarantine`. Record the reason and blocking failure code when
   the test cannot remain core evidence.
4. **Test Artifact Drift Classification**: Classify each affected artifact with
   expectation status, drift status, source, owner, and review evidence. Use
   `no_artifact_expected`, `no_existing_artifact_found`, or blocker drift when
   an artifact is absent.
5. **Acceptance Criteria Traceability Matrix**: Map each current acceptance
   criterion to kept, updated, moved, or planned test evidence. Do not count
   demoted, deleted, quarantined, stale, contradictory, or orphaned tests as
   core coverage.
6. **Assertion Quality Revalidation**: Recheck assertions for observable
   behavior, meaningful failure diagnostics, real boundary coverage, and
   compatibility with the changed expectation.
7. **Determinism and Flakiness Revalidation**: Recheck time, randomness,
   ordering, concurrency, filesystem paths, environment data, snapshots,
   benchmark variance, and external dependencies that could make evidence
   nondeterministic.
8. **Coverage Gap After Reconciliation**: Identify remaining gaps after stale
   tests and unresolved artifact drift are removed from core evidence. Route
   each gap to `test-plan-contract` before `tdd-cycle`.
9. **Removal, Demotion, and Quarantine Evidence**: Record why any test or
   artifact is deleted, demoted, moved out of core evidence, or quarantined,
   including risk, owner, expiry, and recovery trigger.
10. **Reconciliation Contract**: Produce a final contract that names accepted
   core evidence, required updates, blocked items, coverage gaps, downstream
   test contracts, and the exact next step.

## Output

```markdown
## Existing Test Relevance Inventory

| test_id | test_file | linked_acceptance_criteria_ids | previous_expectation | current_expectation | decision | reason | blocking_failure_code | downstream_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TEST-001 |  | AC-001 |  |  | keep |  |  | none |

Allowed `decision` values: `keep`, `update`, `split`, `move`, `demote`, `delete`, `quarantine`.

## Test Artifact Drift Inventory

| artifact_id | artifact_type | artifact_path | linked_test_ids | expected_artifact_policy | expectation_status | drift_status | source_or_generator | owner | blocking_failure_code | review_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-001 | snapshot |  | TEST-001 | artifact required | artifact_expected | reviewed_current |  |  |  |  |

Allowed `expectation_status` values: `artifact_expected`, `no_artifact_expected`, `no_existing_artifact_found`, `blocker_drift`.

## Coverage Gap After Reconciliation

| gap_id | acceptance_criteria_id | missing_or_invalid_evidence | cause | required_test_pattern | downstream_contract_id | owner | blocking_failure_code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GAP-001 | AC-001 |  |  | regression | TPC-001 |  |  |

## Reconciliation Contract

| reconciliation_id | changed_requirement_or_contract | accepted_core_evidence | required_updates | demoted_or_removed_items | quarantined_items | unresolved_blockers | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REC-001 |  |  |  |  |  |  | test-plan-contract |
```

Blocking failure codes include
`new_test_added_without_reconciliation`, `stale_test_counted_as_core`,
`contradictory_test_kept`, `obsolete_test_kept`,
`orphan_test_as_core_coverage`, `false_confidence_test`,
`test_artifact_drift_unresolved`, `snapshot_drift_unreviewed`,
`mock_contract_mismatch`, `quarantined_test_counted_as_evidence`, and
`deletion_without_risk_record`.

## Development work

- Start from the route emitted by `testing-workflow`; do not add new tests for
  changed existing expectations until reconciliation rows exist.
- Prefer the nearest existing test layer and project test pattern when a test
  is kept, updated, split, or moved.
- Treat snapshots, goldens, schema examples, benchmark baselines, and IaC
  expected outputs as test artifacts that need drift review before baseline
  updates are accepted.
- Route unresolved gaps to `test-plan-contract` with linked acceptance
  criteria, artifact drift evidence, fixture governance, and exact commands.

## Non-development work

- Use this skill for review-only reconciliation of plans, test evidence,
  snapshot updates, fixture changes, generated output changes, or coverage
  claims.
- Record absence explicitly: use `no_artifact_expected` when the requirement
  does not need an artifact, `no_existing_artifact_found` when an expected
  artifact is missing, and `blocker_drift` when absence hides unresolved drift.
- Keep deletion, demotion, and quarantine decisions tied to risk and owner
  evidence, not convenience or test pass status.

## Do not

- Do not add new tests before reconciling affected existing tests and artifacts.
- Do not count stale, contradictory, obsolete, orphaned, demoted, deleted, or
  quarantined tests as core evidence.
- Do not update snapshots, goldens, generated expected outputs, schema
  examples, benchmark baselines, or IaC expected outputs without drift review.
- Do not delete or demote tests without recording risk, owner, and replacement
  coverage or accepted residual risk.
- Do not use decision values outside `keep`, `update`, `split`, `move`,
  `demote`, `delete`, and `quarantine`.
