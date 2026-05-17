---
name: verification-gate
description: Use when a completion, correctness, readiness, review, or decision-ready claim needs evidence-backed closure.
metadata:
  short-description: Gate completion claims with evidence
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/verification-gate/SKILL.md -->


# Verification Gate

## Purpose

Create a `Verification Gate` before reporting completion, readiness, correctness, or decision-ready status so every claim is backed by required evidence, spec-plan coverage, and explicit residual risk.

## Workflow

1. State the exact completion claim being considered.
2. List the required evidence IDs from `implementation-evidence`, `source-ledger`, or `claim-evidence-map`.
3. Compare every requirement, spec clause, task, and acceptance criterion against the available evidence.
4. For development work that changes observable behavior, require Scenario Test Contract or Test Plan Contract evidence, or record why tests are not feasible.
5. Require a `Spec-to-Plan Coverage Matrix` when a Spec Ledger exists.
6. List failed items with the command, artifact, or review step that failed.
7. List not-run items separately from failed items.
8. Record residual risks, unrelated known failures, and out-of-scope issues.
9. Set final status to `done`, `done_with_concerns`, `blocked`, or `needs_context`.

## Development work

- Re-run or inspect the exact commands that prove the requested claim before closing.
- Keep unrelated baseline failures separate and name them precisely.
- Verify generated artifacts and source artifacts when both are acceptance criteria.
- Treat missing required test plan, test execution, or test-inapplicable rationale as a failed item, not a residual risk.
- Treat `missing_plan`, `missing_validation`, `missing_evidence`, `stale_evidence`, `unresolved_risk`, `unjustified_fixture`, `fixture_overgrowth`, `missing_real_boundary_check`, and `test_only_behavior` as blockers unless explicitly deferred with owner and reason.

## Non-development work

- Verify source coverage, counterevidence handling, document completeness, and decision traceability.
- Name unsupported assumptions and missing sources before reporting final status.
- Use `done_with_concerns` when the requested deliverable is complete but material residual risk remains.

## Output

```markdown
## Verification Gate

| completion_claim | coverage_report_ids | required_evidence_ids | failed_items | not_run_items | residual_risks | final_status |
| --- | --- | --- | --- | --- | --- | --- |
|  | COVERAGE-001 | EVID-001 |  |  |  |  |
```

## Do not

- Do not report completion without fresh evidence.
- Do not mix unrelated baseline failures into task failure status.
- Do not hide not-run checks under residual risks.
- Do not use `done` when required evidence is missing.
- Do not use `done` when required spec clauses lack plan, validation, evidence, or fixture governance coverage.
