---
name: tdd-cycle
description: Use when writing or modifying tests with test-driven development across any language or technology stack.
metadata:
  short-description: Write correct test code by test type using a TDD workflow.
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/tdd-cycle/SKILL.md -->


# TDD Cycle

## Purpose

Use this skill to write test code through a TDD workflow: define the observable behavior first, write the smallest useful failing test, confirm the failure, add the minimum implementation, confirm the pass, refactor, and record evidence.

Do not force a new test framework. Prefer the project's existing test framework, package manager, directory layout, naming convention, fixture style, assertion helpers, and CI commands.

When the selected testing route requires reconciliation, do not add a new test until `test-suite-reconciliation` has produced a `Reconciliation Contract` and `test-plan-contract` has produced current coverage with the linked `reconciliation_id`.

Use `../../references/downstream-test-contracts.md` when fixture governance,
scenario mapping, canonical TDD Cycle Evidence fields, join rules, allowed
values, or test contract details are needed.

## When to use

- Before completing implementation work that changes behavior or acceptance criteria unless the user explicitly scoped the task as review-only, docs-only, or test-inapplicable and `verification-gate` records that reason.
- Before implementing a new feature when a failing test can express the expected behavior.
- Before fixing a bug when a reproduction test can prove the current failure.
- When adding regression coverage to code with weak or missing tests.
- When validating public API behavior, UI behavior, integration boundaries, schema changes, infrastructure behavior, or other observable behavior.
- When the user asks for TDD, test first, test code writing, or test type selection.

## Inputs to inspect

- Requirement, bug report, acceptance criteria, or behavior description.
- Existing tests near the target code, including naming, layout, assertion style, fixtures, fakes, stubs, mocks, skipped tests, disabled assertions, `.only` markers, and snapshot update practices.
- Build files, package manager files, CI workflows, test scripts, and local verification commands.
- Production entry points and public interfaces that expose the behavior under test.
- External boundaries such as time, randomness, network, filesystem, process, database, browser, cloud, queue, identity, and concurrency.
- Existing documentation, references, or examples that define expected behavior.

## Workflow

1. Restate the requirement as one observable behavior that a user, caller, client, operator, or system boundary can see.
2. Detect the stack, existing test tools, nearest existing test layer, test file placement, naming conventions, and command style.
3. Use the nearest existing test layer by default. Check `references/testing-patterns.md` only when the behavior boundary is unclear, the existing layer is a poor fit, or the work needs contract, property, snapshot, performance, security, accessibility, migration, or infrastructure validation.
4. For reconciliation-required work, confirm the `reconciliation_id`, accepted core evidence, residual gaps, and replacement coverage from the current coverage contract before writing or modifying tests.
5. Write the smallest failing test with inline minimal arrange first; extract a fixture only when repeated arrange becomes clearer with a precise name and the Fixture Governance Contract approves it.
6. Run the narrowest command and confirm the intended failure message proves the missing behavior, not a syntax, import, environment, or setup error.
7. Add the minimum implementation needed to pass the failing test.
8. Run the same command and confirm the test passes for the intended behavior.
9. Refactor production and test code only while keeping the test suite green.
10. Add boundary, negative, regression, accessibility, security, or performance cases only when the risk justifies them.
11. Record `TDD Cycle Evidence` with the `reconciliation_id` when applicable, failing command, observed failure, passing command, observed result, and any gaps; use the canonical join rules in `downstream-test-contracts.md`.
12. Prepare a reviewer handoff only when review is requested, the parent task asks for one, or a TDD evidence claim needs review.
13. Report the detected stack, selected or reused test layer, commands run, evidence, risks, and next verification needs.

## Test type decision matrix

Use this as a quick selector, not as a required classification ceremony. Start with the nearest existing test layer and use `references/testing-patterns.md` for detailed rules only when the right layer is unclear or specialized coverage is needed.

| Test type | Use when | First failing test shape |
| --- | --- | --- |
| Unit | One function, class, module, or domain rule can be tested without real external services. | One input, state transition, validation rule, or error outcome fails through a public API. |
| Integration | Multiple project components must work together across a real local boundary. | One boundary interaction fails, such as write then read, route then handler, or serializer then parser. |
| Contract | Consumer and provider must agree on request, response, message, event, or schema compatibility. | One missing or changed contract example fails against the consumer or provider verifier. |
| Component | A UI, service component, or composable unit should be tested through public inputs and visible outputs. | One rendered or emitted behavior fails through the component's public boundary. |
| End-to-end | Confidence depends on a full user or system journey across the application boundary. | One shortest critical path fails through public interfaces. |
| Smoke | A build, deployment, service, or environment needs a fast alive check. | One essential route, startup, health, auth, or representative happy path check fails. |
| Regression | A known bug, incident, or review finding must remain fixed. | One minimal reproduction of the previous observable failure fails before the fix. |
| Characterization | Existing behavior must be captured before refactoring or migration. | One public legacy behavior is documented by a focused expectation. |
| Property-based | A behavior must satisfy invariants across generated inputs. | One invariant or concrete counterexample fails before broadening generation. |
| Snapshot/Golden | Stable structured output or generated artifacts must be reviewed for unintended changes. | One deterministic artifact differs from the approved baseline for a meaningful reason. |
| Performance/Benchmark | Latency, throughput, memory, allocation, startup, or scalability is an explicit requirement. | One controlled workload exceeds a documented budget or accepted baseline. |
| Security | Auth, input validation, secrets, isolation, cryptography, or abuse resistance can regress. | One exploit, unsafe default, or policy violation succeeds before the fix. |
| Accessibility | Behavior affects semantic, keyboard, focus, announcement, or assistive technology outcomes. | One user-observable accessibility behavior fails through roles, names, or controls. |
| Migration/Schema | Data, schema, API, configuration, or backward compatibility can break existing states. | One legacy state, migration, rollback, or invalid schema case fails. |
| Infrastructure/IaC validation | Infrastructure definitions, policies, permissions, networking, or runtime settings can be validated before deployment. | One plan, rendered config, policy, or invariant assertion fails without applying real infrastructure. |

## Test writing rules

- Use Arrange-Act-Assert or Given-When-Then so setup, behavior, and assertion are easy to separate.
- Test one observable behavior per test and prefer public behavior over private helpers, internal state, call order, CSS internals, or implementation-detail-only assertions.
- Write concrete assertions for values, state, errors, rendered output, persisted data, emitted events, permissions, or generated artifacts; avoid assertions that only prove code executed.
- Start the first failing test with inline minimal arrange. Use fixtures only when repeated arrange is clearer with a name, and keep each fixture narrow enough that unused setup does not hide intent.
- Prefer real domain objects and local collaborators when they are fast, deterministic, and inside the behavior boundary.
- Apply the Fixture Governance Contract before adding or expanding any fixture, mock, fake, stub, snapshot, seed record, generated input, or test-only adapter.
- Treat the fixture budget as `0` by default and require an explicit approved exception when the test needs a double or shared setup.
- Prefer a high-fidelity boundary such as a public API, CLI, parser, local persistence boundary, component render, or integration adapter before using doubles.
- Use a fake for a lightweight working substitute, a stub for fixed external answers or errors, and a mock only when the outbound interaction contract itself is the requirement.
- Do not assert only that a mock was called when the user-visible behavior can be asserted.
- Do not create broad fixture factories before proving repeated setup is clearer with a named fixture.
- Do not allow `unjustified_fixture`, `fixture_overgrowth`, `missing_real_boundary_check`, or `test_only_behavior` to pass as valid coverage.
- Do not count tests without an Acceptance Criteria ID as core scenario coverage.
- Do not report completion without the exact failing and passing test commands.
- Mock external boundary only: time, random, network, filesystem, process, database outside the chosen boundary, browser, cloud API, queue, payment, identity provider, or concurrency coordination.
- Make time, randomness, network, filesystem, process environment, locale, ordering, generated IDs, ports, and concurrency deterministic.
- Do not use sleep, real external services, production credentials, shared mutable state, order dependence, broad hidden fixtures, or ambient production data in routine tests.
- Snapshot or golden tests need deterministic input, normalized noise, small reviewed baselines, and a clear reason for accepting changes.
- Performance tests need a stated budget or baseline, controlled workload, isolated measurement assumptions, and reporting that separates correctness from noisy timing.
- Security tests need attacker-relevant preconditions, public boundary execution, neutral credentials, and explicit denial, sanitization, isolation, redaction, or safe-failure assertions.

## Stack detection rules

- Node/TypeScript: inspect `package.json`, lockfiles, `tsconfig`, test scripts, and existing Jest, Vitest, Mocha, Playwright, Cypress, Testing Library, or Node test runner usage.
- Python: inspect `pyproject.toml`, `pytest.ini`, `tox.ini`, `noxfile.py`, `requirements`, and existing pytest, unittest, Hypothesis, factory, fixture, or monkeypatch patterns.
- Java/Kotlin: inspect Gradle or Maven files, source sets, JUnit, TestNG, Mockito, AssertJ, Spring test, Kotest, or Spek conventions.
- Go: inspect `go.mod`, `_test.go` files, table tests, `testing`, testify, gomock, integration tags, and race or benchmark commands.
- Rust: inspect `Cargo.toml`, unit modules, integration test directories, `cargo test`, proptest, criterion, feature flags, and snapshot tools.
- .NET: inspect solution and project files, xUnit, NUnit, MSTest, FluentAssertions, Moq, Verify, and `dotnet test` settings.
- Ruby: inspect Gemfile, RSpec, Minitest, Rails test structure, factories, VCR, and rake tasks.
- PHP: inspect Composer, PHPUnit, Pest, Laravel or Symfony test utilities, database refresh patterns, and test bootstrap files.
- Swift: inspect Package.swift, XCTest, Swift Testing, Xcode schemes, UI test targets, and simulator requirements.
- C/C++: inspect CMake, Make, Bazel, Meson, GoogleTest, Catch2, doctest, CTest, sanitizers, and benchmark harnesses.
- SQL: inspect migration folders, schema tests, dbt tests, stored procedure checks, seed data, and database-specific test harnesses.
- Terraform: inspect modules, provider locks, `terraform validate`, plan checks, policy tools, tflint, and terratest usage.
- Docker/Kubernetes: inspect Dockerfiles, Compose files, Helm charts, Kustomize overlays, manifests, kubeconform, conftest, and dry-run validation commands.

## Development work

- Treat needed tests as part of the implementation, not optional follow-up, when a Requirement Packet, Spec Contract, or Plan Contract changes observable behavior.
- If no automated test is feasible, record the scenario, reason, manual/inspection evidence, and residual risk in `test-plan-contract` and `verification-gate`.
- Read nearby production and test code before writing tests so the new test follows existing framework, naming, helpers, and command conventions.
- Add the test in the nearest existing layer that can fail for the required behavior, not in a broader or narrower layer for convenience.
- Keep the first failing test small and diagnostic; broaden coverage only after the intended failure and pass are proven.
- Keep production changes minimal until the selected failing test passes, then refactor with the same tests still green.
- Keep fixture growth below the approved fixture budget and record drift checks for any retained fixture.
- Include the reviewer handoff only when review is needed, the parent task asks for it, or a claimed TDD cycle needs independent review.

## Non-development work

This skill is not the default workflow for documentation, strategy, research, planning, or review-only tasks.

Route unclear requirements to `requirements-packet`, source-backed investigation to `research-plan`, artifact review to `claim-evidence-map`, and completion claims to `verification-gate`.

Use this skill for non-development work only when the requested artifact is itself test-writing guidance, a test plan, or a TDD review checklist.

## Review handoff

Provide this optional reviewer handoff only when review is needed, the parent task asks for it, or a TDD evidence claim needs review:

```text
reviewer handoff
- original requirement or bug report:
- detected stack:
- selected test type and rationale:
- changed production files:
- changed test files:
- failing test command and observed failure:
- passing test command and observed result:
- behavior under test:
- edge/failure/regression cases covered:
- test gaps intentionally left open:
- known runtime/environment limitations:
```

## Output

## TDD Cycle Evidence

| tdd_evidence_id | scenario_id | acceptance_criteria_id | reconciliation_id | test_file | failing_command | observed_failure | passing_command | observed_result | residual_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TDD-001 | SCN-001 | AC-001 | REC-001 |  |  |  |  |  | none |

## Scenario Test Contract

| Scenario ID | Acceptance Criteria ID | Test Layer | Test File | Command | Fixture/Mock Policy | Evidence ID |
| --- | --- | --- | --- | --- | --- | --- |

## Fixture/Mock Justification

| Name | Type | Needed Because | Real Alternative Considered | Behavior Hidden | Decision |
| --- | --- | --- | --- | --- | --- |

## Fixture Governance Contract

| fixture_id | linked_scenario_ids | linked_spec_clause_ids | fixture_type | real_boundary_preferred | justification | owner | drift_check | expiry_or_update_trigger |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

- detected stack
- selected test type
- reason for selected test type
- test file path
- test cases added or proposed
- commands run
- failing evidence
- passing evidence
- reviewer handoff, when review is requested
- risks or untested gaps

## Do not

- Do not ignore the existing framework, runner, assertion style, fixtures, naming, directories, or CI commands.
- Do not write flaky tests that depend on sleep, real external services, production data, order dependence, uncontrolled time, uncontrolled random values, shared state, or ambient environment.
- Do not write implementation-detail-only tests that verify private helpers, incidental call order, internal state, or coverage without behavior.
- Do not leave `.only`, focused tests, skipped tests, disabled assertions, broad snapshots, or tests that cannot fail for the requirement.
- Do not add a new test for changed existing requirements until reconciliation results and current coverage identify the gap or replacement coverage.
- Do not implement production behavior before confirming the intended failure of the failing test.
- Do not put secrets, production credentials, internal endpoints, private customer data, or live tokens into fixtures, snapshots, logs, or test output.
- Do not omit failing evidence, passing evidence, or selected test layer rationale when claiming TDD work is complete.
- Do not omit the reviewer handoff when review is requested, the parent task asks for it, or TDD evidence is claimed for review.
