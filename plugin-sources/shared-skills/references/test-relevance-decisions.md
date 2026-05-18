# Test Relevance Decisions

Use this reference from `test-suite-reconciliation` when a changed requirement
or contract may invalidate existing tests.

## Decision Schema

Each existing test gets exactly one decision. The only allowed values are
`keep`, `update`, `split`, `move`, `demote`, `delete`, and `quarantine`.

| decision | use_when | required_evidence | blocking_failure_if_wrong |
| --- | --- | --- | --- |
| `keep` | The test still proves current acceptance criteria through observable behavior. | Linked acceptance criteria, assertion review, deterministic command. | `stale_test_counted_as_core` |
| `update` | The test remains relevant but its arrange, assertion, fixture, or artifact expectation must change. | Previous expectation, current expectation, exact update needed. | `false_confidence_test` |
| `split` | One test mixes still-valid coverage with stale, contradictory, or unrelated coverage. | New target test IDs and criteria mapping for each piece. | `contradictory_test_kept` |
| `move` | The test belongs in a different layer, file, or contract boundary. | Destination, reason, command, preserved acceptance criteria link. | `orphan_test_as_core_coverage` |
| `demote` | The test may remain useful as characterization, smoke, or non-core signal but cannot prove current criteria. | New evidence role and residual risk. | `stale_test_counted_as_core` |
| `delete` | The test proves obsolete behavior and should not remain as suite noise. | Risk record, replacement coverage or accepted residual risk. | `deletion_without_risk_record` |
| `quarantine` | The test may be valid but is currently nondeterministic, environment-bound, or blocked by unresolved artifact drift. | Owner, expiry, recovery trigger, exclusion from core evidence. | `quarantined_test_counted_as_evidence` |

## Existing Test Relevance Inventory

```markdown
| test_id | test_file | linked_acceptance_criteria_ids | previous_expectation | current_expectation | decision | reason | blocking_failure_code | downstream_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TEST-001 | tests/example_test.py | AC-001 | old error is accepted | new error is rejected | update | assertion still targets obsolete behavior | false_confidence_test | test-plan-contract |
```

## Failure Terms

- `new_test_added_without_reconciliation`: a changed existing expectation got
  new tests before existing tests and artifacts were reconciled.
- `stale_test_counted_as_core`: a stale test remained in completion evidence.
- `contradictory_test_kept`: a test that conflicts with current expectations
  remained active without split, update, demotion, deletion, or quarantine.
- `obsolete_test_kept`: a test for removed behavior stayed in the active suite.
- `orphan_test_as_core_coverage`: a test without current acceptance criteria
  mapping was counted as core coverage.
- `false_confidence_test`: a weak assertion or hidden fixture made the test
  pass without proving the current behavior.
- `mock_contract_mismatch`: a mock, fake, or stub no longer matches the real
  contract it claims to represent.

## Review Rules

- Do not infer relevance from passing status alone.
- Do not keep a test as core evidence without current acceptance criteria.
- Do not delete, demote, or quarantine a test without owner and risk evidence.
