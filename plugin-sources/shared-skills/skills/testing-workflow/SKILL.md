---
name: testing-workflow
description: Use when starting any testing-related work so the request is routed to the correct downstream testing skill or reviewer before tests are written or reviewed.
metadata:
  short-description: Route testing work through the required shared-skills entry point.
---

# Testing Workflow

## Purpose

Use this skill as the single entry point for test planning, test writing, test result review, artifact drift review, and test-inapplicable decisions.

The goal is to classify the testing request before work begins, output a `Testing Workflow Route`, and then invoke the named downstream skill or reviewer. When the request may change existing requirements, public contracts, schemas, migrations, bug expectations, security policy, performance budgets, or generated artifact contracts, do not add new tests until reconciliation is complete.

Use `../../references/downstream-test-contracts.md` when fixture governance, scenario mapping, or test contract details are needed.
Use `../../references/test-assertion-quality.md`,
`../../references/language-test-smells.md`, and
`../../references/testing-patterns.md` when routing downstream application
project tests that must prove observable behavior or an explicit artifact contract
without weak assertions, implementation-detail assertions, or flaky shared-state
evidence.

## Workflow

1. Identify whether the request asks for new behavior coverage, existing requirement or contract changes, artifact drift review, review-only feedback, or a test-inapplicable decision.
2. Check whether the requested work changes an existing requirement, public API, schema, migration, bug expectation, security policy, performance budget, generated artifact contract, or expected artifact baseline.
3. Select exactly one route from the route table.
4. For routes that write, modify, plan, or review downstream application
   project tests, require `Behavior Boundary Classification`,
   `Assertion Quality Gate`, and `TDD Quality Evidence` before accepting core
   coverage.
5. Output the `Testing Workflow Route` table before adding, changing, accepting, or rejecting tests.
6. Continue only through the route's next step.
7. Record unresolved routing ambiguity as `Reconciliation Required`.

## Testing Workflow Route Table

| route | use_when | next_step |
| --- | --- | --- |
| New Behavior Coverage | The work adds coverage for a new feature and does not change existing requirements or public contracts. | `scenario-test-designer -> test-plan-contract -> tdd-cycle` |
| Reconciliation Required | The work changes an existing requirement, public API, schema, migration, bug expectation, security policy, performance budget, or generated artifact contract. | `test-suite-reconciliation -> test-plan-contract -> tdd-cycle` |
| Artifact Drift Review | The changed scope is a fixture, mock, fake, stub, snapshot, golden, seed, cassette, generated expected output, schema example, benchmark baseline, or IaC expected output. | `test-suite-reconciliation` |
| Review Only | The request asks to review reconciliation evidence, existing test relevance, artifact drift, coverage claims, deletion/demotion/quarantine evidence, newly written or modified test adequacy, a test plan, or test results without writing or changing tests. | `test-reconciliation-reviewer` for reconciliation evidence, existing test relevance, artifact drift, stale/obsolete/contradictory/orphan/false-confidence coverage claims, deletion/demotion/quarantine evidence, reconciliation/current-coverage test plans, or test results for that evidence; `test-adequacy-reviewer` for newly written or modified test assertion quality, behavior boundary, fixture/mock justification, determinism, executable test adequacy, new/modified test plans, or test results for those tests |
| Test Inapplicable | Automated tests are impossible or inappropriate for the accepted requirement and the reason must be recorded. | `test-plan-contract -> verification-gate` |

## Output

```markdown
## Testing Workflow Route

| route_id | request_summary | behavior_change_type | existing_tests_may_be_affected | selected_route | required_next_skill_or_agent | reason | residual_risk_if_skipped |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ROUTE-001 |  |  |  |  |  |  |  |
```

## Development work

- Prefer `New Behavior Coverage` only when the work is additive and leaves existing behavior, public contracts, and artifact baselines unchanged.
- Use `Reconciliation Required` before writing tests whenever the requested change updates prior expectations or compatibility promises.
- Use `Artifact Drift Review` when the test artifact itself may hide behavior drift or require approval before a baseline changes.
- Use the assertion quality references when selecting or reviewing tests so
  downstream application coverage proves observable behavior or an explicit artifact contract, not implementation details or coverage activity.
- Use `Test Inapplicable` only after `test-plan-contract` records why automation is not feasible and `verification-gate` records residual risk.

## Non-development work

- Use `Review Only` when the task is limited to assessing a plan, test result, coverage claim, or reconciliation evidence.
- Under `Review Only`, choose `test-reconciliation-reviewer` for reconciliation evidence, existing test relevance, artifact drift, stale, obsolete, contradictory, orphaned, false-confidence coverage claims, deletion, demotion, quarantine evidence, reconciliation/current-coverage test plans, and test results for that evidence.
- Under `Review Only`, choose `test-adequacy-reviewer` for newly written or modified test assertion quality, behavior boundary coverage, fixture/mock justification, determinism, executable test adequacy, new/modified test plans, and test results for those tests.
- Keep route rationale tied to the user's request and the affected contract or artifact, not to implementation convenience.
- Ask for requirement clarification instead of selecting `New Behavior Coverage` when the request conflicts with existing documented expectations.

## Do not

- Do not bypass this skill for testing-related work.
- Do not add tests for changed existing requirements or public contracts before reconciliation.
- Do not update snapshots, goldens, fixtures, mocks, seeds, cassettes, or generated expected outputs without artifact drift review.
- Do not route review-only work into test writing.
- Do not claim tests are inapplicable without a recorded reason and verification-gate residual risk.
