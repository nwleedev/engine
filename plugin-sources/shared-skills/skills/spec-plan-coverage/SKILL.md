---
name: spec-plan-coverage
description: Use when a Spec Ledger, Plan Contract, Test Plan Contract, implementation evidence, or completion claim needs clause-level coverage validation before work is called done.
metadata:
  short-description: Validate spec clause coverage before completion
---

# Spec Plan Coverage

## Purpose

Create a clause-level coverage report that proves whether a plan, test plan,
implementation evidence packet, or completion claim fully reflects the spec.
Use this skill to turn a spec into a `Spec Ledger`, then compare that ledger
against plan tasks, scenario tests, validation commands, evidence, and residual
risk before implementation or closure.

This skill is for evidence-backed workflow control. It is not a general advice
checklist.

Use `../../references/workflow-artifacts.md` when table schemas, row-level rules, or coverage status values are needed.

## Workflow

1. Extract every behavior, artifact, failure mode, compatibility constraint,
   non-goal, assumption, and required validation from the source spec into a
   `Spec Ledger` with stable `spec_clause_id` values and `source_location`
   references.
2. Mark each clause with `validation_intent`: automated test, generated
   artifact validation, static inspection, manual protocol, research evidence,
   review gate, deferred decision, or not applicable with reason.
3. Compare every clause against the Plan Contract and require each plan task to
   list `linked_spec_clause_ids`.
4. Compare behavior-changing clauses against Scenario Test Contract, Test Plan
   Contract, Fixture Governance Contract, and TDD evidence when tests are
   expected.
5. Compare completed clauses against Implementation Evidence and Verification
   Gate rows.
6. Produce a `Spec-to-Plan Coverage Matrix` with one `coverage_status` per
   clause: `covered`, `missing_plan`, `missing_validation`,
   `missing_evidence`, `stale_evidence`, `unresolved_risk`,
   `deferred_with_owner`, or `not_applicable_with_reason`.
7. Fail the gate when any required clause or task has `orphan_task`,
   `needs_spec_mapping`, `missing_plan`, `missing_validation`,
   `missing_fallback`, `missing_evidence`, `stale_evidence`,
   `unresolved_risk`, `not_run_hidden`, `missing_review_gate`,
   `unjustified_fixture`, `stale_fixture`, `fixture_overgrowth`, `unapproved_mock`,
   `missing_real_boundary_check`, or `test_only_behavior`.
8. Emit both a machine-readable JSON report and a redacted Markdown summary
   when source specs or plans are confidential and cannot be committed.
9. When a machine check is needed, run `validate_spec_plan_coverage.py` against
   a redacted JSON intermediate artifact. The script exits `0` only for
   `done_candidate`; blocker reports exit `1`.

## Development work

- Run this before implementation when the plan is derived from a spec and again
  before claiming completion.
- Require plan tasks, test scenarios, validation commands, evidence IDs, and
  review findings to cite `spec_clause_id` values instead of only broad spec
  IDs.
- Treat fixture-heavy tests as incomplete when the Fixture Governance Contract
  does not prove a high-fidelity boundary, approved fixture budget, drift check,
  and real-boundary alternative.
- Record uncommitted or confidential specs by stable local path, document
  heading, paragraph marker, or redacted source label in `source_location`.

## Non-development work

- Use this for research packets, architecture decisions, review documents,
  migration plans, and process changes when a spec or decision record must be
  fully reflected by a plan.
- Treat evidence as source IDs, review records, artifact diffs, decision logs,
  or repeatable inspection steps when code tests do not apply.
- Mark confidential source text as redacted, but keep stable IDs and enough
  source location detail for the current project owner to audit the mapping.

## Output

```markdown
## Spec Ledger

| spec_clause_id | linked_requirement_ids | source_location | clause_type | validation_intent | priority | confidentiality | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-001.CLAUSE-001 | REQ-001 | spec.md#section | behavior | automated test | must | redacted | open |  |

## Spec-to-Plan Coverage Matrix

| spec_clause_id | linked_requirement_ids | plan_task_ids | scenario_ids | test_or_check_ids | evidence_ids | coverage_status | gap_or_risk | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-001.CLAUSE-001 | REQ-001 | TASK-001 | SCN-001 | TEST-001 | EVID-001 | missing_evidence |  |  |
```

Also produce a machine-readable JSON report and a redacted Markdown summary
when the underlying spec, plan, or evidence cannot be committed.

```markdown
## Coverage Report

| coverage_report_id | matrix_id | validator_command | validator_exit_code | report_path | redacted_markdown_path | blocking_codes | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| COVERAGE-001 | MATRIX-001 |  | 1 |  |  | missing_evidence | blocked |
```

Validator command shape:

```bash
python3 validate_spec_plan_coverage.py redacted-workflow.json --json-output coverage-report.json --markdown-output coverage-report.md
```

## Do not

- Do not approve a plan that omits required `linked_spec_clause_ids`.
- Do not collapse multiple spec clauses into one row when they require
  different validation, evidence, or risk handling.
- Do not mark a clause `covered` when it only has a plan task and no validation
  or evidence.
- Do not treat broad fixture, mock, or snapshot tests as coverage without a
  Fixture Governance Contract.
- Do not expose confidential spec text in committed reports, logs, or generated
  public plugin artifacts.
