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
| `expected` | The current requirement needs an artifact or baseline. | Artifact path, generator or source, linked test IDs, owner. | Missing or stale artifact blocks core evidence. |
| `no_artifact_expected` | The current requirement is proven without any artifact. | Reason the behavior is covered by assertions, command, or manual inspection. | Do not create a placeholder artifact. |
| `unknown_expected` | The workflow cannot yet prove whether the current requirement needs an artifact. | Search locations, decision owner, and follow-up needed to classify expected vs not expected. | Blocks completion until resolved or recorded as residual risk. |
| `found` | An artifact exists but its current role still needs drift classification. | Artifact path, linked tests, and source or generator when known. | Cannot count as core evidence until drift status is current. |

## Test Artifact Drift Inventory

```markdown
| artifact_id | artifact_type | path | used_by_tests | current_role | expectation_status | drift_status | required_action | drift_reason | owner_or_followup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-001 | schema example | docs/schema/user.json | TEST-001 | API compatibility baseline | expected | drifted | update | schema diff conflicts with current contract | platform |
| ART-002 | benchmark baseline | benchmarks/login.json | TEST-002 | performance budget tracked elsewhere | no_artifact_expected | not_applicable | keep external evidence | covered by p95 dashboard | perf |
| ART-003 | IaC expected output | infra/expected/plan.json | TEST-003 | IaC plan baseline | expected | no_existing_artifact_found | create or document residual risk | search found no current expected output | infra |
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
- `no_existing_artifact_found`: an artifact is expected or expectation is still
  unknown, but no existing artifact was found after a documented search.
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
