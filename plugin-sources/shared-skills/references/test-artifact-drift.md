# Test Artifact Drift

Use this reference from `test-suite-reconciliation` when a fixture, mock, fake,
stub, snapshot, golden, seed, cassette, generated expected output, schema
example, benchmark baseline, or IaC expected output may no longer match the
current requirement or project boundary.

## Expectation Schema

Artifact absence must be classified explicitly so missing artifacts do not hide
coverage gaps.

| expectation_status | use_when | evidence_required | blocking_behavior |
| --- | --- | --- | --- |
| `artifact_expected` | The current requirement needs an artifact or baseline. | Artifact path, generator or source, linked test IDs, owner. | Missing or stale artifact blocks core evidence. |
| `no_artifact_expected` | The current requirement is proven without any artifact. | Reason the behavior is covered by assertions, command, or manual inspection. | Do not create a placeholder artifact. |
| `no_existing_artifact_found` | An artifact is expected but none exists yet. | Search locations, required downstream contract, owner. | Treat as coverage gap until created or justified. |
| `blocker_drift` | Artifact absence or mismatch prevents trustworthy evidence. | Drift description, blocked criteria, owner, recovery trigger. | Blocks completion as `test_artifact_drift_unresolved`. |

## Test Artifact Drift Inventory

```markdown
| artifact_id | artifact_type | artifact_path | linked_test_ids | expected_artifact_policy | expectation_status | drift_status | source_or_generator | owner | blocking_failure_code | review_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-001 | schema example | docs/schema/user.json | TEST-001 | artifact required for API compatibility | artifact_expected | drifted | schema generator | platform | test_artifact_drift_unresolved | diff reviewed |
| ART-002 | benchmark baseline | benchmarks/login.json | TEST-002 | performance budget tracked elsewhere | no_artifact_expected | not_applicable | p95 dashboard | perf |  | linked evidence |
| ART-003 | IaC expected output | infra/expected/plan.json | TEST-003 | IaC expected output required | no_existing_artifact_found | missing | terraform plan | infra | test_artifact_drift_unresolved | search log |
```

## Drift Classes

- `no_drift`: artifact matches the current requirement and its source or
  generator is recorded.
- `reviewed_current`: artifact changed and the diff was reviewed against the
  current requirement.
- `drifted`: artifact conflicts with the current requirement or project
  boundary and cannot support core coverage.
- `unreviewed`: snapshot, golden, schema example, benchmark baseline, or IaC
  expected output changed without human or automated review.
- `missing`: an expected artifact was not found.
- `not_applicable`: no artifact is expected for the requirement.

## Failure Terms

- `test_artifact_drift_unresolved`: artifact drift remains unresolved while the
  affected test is counted as evidence.
- `snapshot_drift_unreviewed`: a snapshot or golden diff was accepted without
  review evidence.
- `mock_contract_mismatch`: a mock, fake, stub, cassette, or generated fixture
  no longer matches the real boundary or current contract.
- `false_confidence_test`: artifact contents make the test pass without
  asserting current observable behavior.

## Review Rules

- Do not treat generated output as current just because it was regenerated.
- Do not accept schema example, benchmark baseline, or IaC expected output drift
  without linking the changed requirement or contract.
- Do not count an artifact-backed test as core evidence while its artifact row
  has `blocker_drift`, `drifted`, `unreviewed`, or `missing` status.
