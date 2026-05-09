# TDD Test Types

Use this reference from `tdd-test-writing` when choosing the smallest useful failing test for a requested behavior.

## Test double priority

- Start with inline minimal arrange so the first failing test states its own preconditions clearly.
- Use real domain objects and local collaborators when they are fast, deterministic, and inside the behavior boundary.
- Use a fake when a lightweight working substitute is enough, such as an in-memory repository or local queue that behaves like the real boundary without production cost.
- Use a stub when the test only needs fixed external answers, errors, or edge responses and does not need to verify how the dependency was called.
- Use a mock only when the outbound interaction contract itself is the requirement; avoid mocks for simple return-value, state, or rendered-output verification.
- Extract fixtures only when repeated arrange becomes clearer with a name, and keep each fixture narrow enough that unused setup does not hide test intent.

## Unit

- **When to use:** Use a unit test when one function, class, module, or domain rule can be exercised without real external services.
- **What to verify:** Verify observable return values, state transitions, emitted domain events, validation outcomes, and error behavior at the smallest useful boundary.
- **What to avoid:** Avoid private helper calls, incidental branches, broad integration behavior, real network calls, and brittle call-order assertions.
- **Test code structure:** Use Arrange-Act-Assert or Given-When-Then with the minimum local setup needed to expose the behavior.
- **Assertion standard:** Assert concrete outputs and failure modes, including boundary, negative, and regression cases when the risk justifies them.
- **Fixture, mock, stub, fake use:** Start inline with real domain objects, use a fake for a small local substitute such as an in-memory repository, use a stub for fixed external answers such as clock or random values, and use a mock only when the required behavior is an outbound call contract.
- **Flaky test prevention:** Control time, randomness, locale, ordering, filesystem paths, and concurrency instead of sleeping or depending on test order.
- **TDD first failing test:** Write one smallest missing behavior, such as one invalid input returning the required error.
- **Use existing project tools first:** Follow the existing unit test framework, file placement, naming, parameterization, and assertion helpers before adding new patterns.

## Integration

- **When to use:** Use an integration test when two or more project components must work together across a real boundary such as database access, routing, serialization, storage adapters, or service wiring.
- **What to verify:** Verify data crossing the boundary, transaction behavior, serialization format, adapter configuration, and failure propagation.
- **What to avoid:** Avoid full user journeys, private implementation details inside each component, and third-party services that can be replaced by a local test double.
- **Test code structure:** Build the smallest real integration slice and isolate systems outside that slice with project-approved local harnesses.
- **Assertion standard:** Assert boundary-visible outcomes such as persisted records, emitted responses, returned data transfer objects, or normalized errors.
- **Fixture, mock, stub, fake use:** Prefer real local collaborators inside the integration boundary, use fixtures only for repeated environment setup, use fakes for local substitutes outside the slice, use stubs for fixed external service responses, and reserve mocks for required outbound protocol calls.
- **Flaky test prevention:** Reset state per test, use isolated schemas or directories, avoid shared ports, avoid real clocks, and clean resources deterministically.
- **TDD first failing test:** Drive one interaction that currently fails at the boundary, such as persisting then reading the expected record.
- **Use existing project tools first:** Reuse existing integration fixtures, database setup, local service harnesses, and CI-compatible commands before introducing new infrastructure.

## Contract

- **When to use:** Use a contract test when a provider and consumer must agree on request, response, message, schema, or event compatibility.
- **What to verify:** Verify required fields, optional fields, status or error semantics, encoding, version compatibility, and backward-compatible behavior.
- **What to avoid:** Avoid testing provider internals, duplicating full integration suites, or asserting fields the consumer does not rely on.
- **Test code structure:** Define the consumer expectation or shared schema first, then verify the provider and consumer against that contract with the smallest representative examples.
- **Assertion standard:** Assert explicit compatibility rules and meaningful mismatch diagnostics rather than broad snapshots of entire payloads.
- **Fixture, mock, stub, fake use:** Use minimal inline contract examples and real schema objects first, use fakes only when a provider simulator implements the contract realistically, use stubs for canned provider states, and use mocks only when the contract requires verifying a specific outbound request.
- **Flaky test prevention:** Pin contract versions, normalize generated fields, avoid real remote providers in routine tests, and make serialization deterministic.
- **TDD first failing test:** Add one contract example for the missing or changed interaction that fails until both sides honor it.
- **Use existing project tools first:** Prefer the repository's existing schema validators, contract harnesses, API clients, and fixture conventions before adding a new contract tool.

## Component

- **When to use:** Use a component test when a UI, service component, or composable unit should be tested through its public inputs and user-visible outputs while still isolated from the full application.
- **What to verify:** Verify rendered behavior, emitted events, public callbacks, validation messages, accessibility-relevant output, and state changes visible through the component boundary.
- **What to avoid:** Avoid asserting private state, styling implementation details, framework internals, or child component internals that are not part of the public contract.
- **Test code structure:** Render or instantiate the component with the smallest realistic inputs, perform the user or caller action, and assert the externally visible result.
- **Assertion standard:** Assert what a user, caller, or parent component can observe, using semantic queries or public APIs when the stack supports them.
- **Fixture, mock, stub, fake use:** Start with inline props and real child components, use fakes for lightweight stores or routers that behave like the real shell, use stubs for fixed API or timer responses, and use mocks only for required emitted callbacks or outbound analytics contracts.
- **Flaky test prevention:** Wait on stable observable state, avoid animation timing assumptions, reset global component state, and isolate mounted instances per test.
- **TDD first failing test:** Start with one missing visible behavior, such as submitting invalid input and seeing the expected validation message.
- **Use existing project tools first:** Use the project's established component test renderer, semantic query helpers, accessibility helpers, and state setup conventions.

## End-to-end

- **When to use:** Use an end-to-end test when confidence depends on a complete user or system journey across the deployed or production-like application boundary.
- **What to verify:** Verify critical path behavior, realistic navigation or workflow completion, system integration, durable side effects, and user-visible failure recovery.
- **What to avoid:** Avoid covering every edge case, asserting implementation details, relying on unrelated third-party availability, or using E2E tests as a substitute for lower-level tests.
- **Test code structure:** Set up only the required initial state, drive the journey through public interfaces, and assert the final observable outcome.
- **Assertion standard:** Assert stable user-visible or externally visible results such as page content, notifications, stored records, delivered messages, or API-visible state.
- **Fixture, mock, stub, fake use:** Keep journey setup inline or through narrow seed fixtures, use real application components, use fakes for approved local external services such as mail or payment sandboxes, use stubs for fixed third-party responses, and use mocks only when verifying a required outbound integration call.
- **Flaky test prevention:** Use deterministic test data, isolated accounts or tenants, resilient selectors or public APIs, explicit readiness signals, and cleanup that does not depend on test order.
- **TDD first failing test:** Add one shortest critical journey that fails at the missing behavior, such as completing checkout until the expected confirmation appears.
- **Use existing project tools first:** Use existing browser, mobile, API, seed, environment, and CI E2E tooling before adding another runner or harness.

## Smoke

- **When to use:** Use a smoke test when a build, deployment, service, or environment needs a fast check that essential capabilities are alive.
- **What to verify:** Verify startup, health endpoints, critical routes, basic authentication or connectivity, and one representative happy path.
- **What to avoid:** Avoid deep business logic coverage, exhaustive assertions, heavy fixtures, and slow or destructive workflows.
- **Test code structure:** Run a short sequence of top-level checks with clear failure messages and minimal arrange.
- **Assertion standard:** Assert only the few signals that prove the system is usable enough for the next verification stage.
- **Fixture, mock, stub, fake use:** Use real local or deployed smoke targets when safe, avoid fixtures beyond named environment setup, use fakes for unsafe local substitutes, use stubs for fixed dependency health responses, and avoid mocks unless the smoke requirement is that a probe calls an outbound dependency.
- **Flaky test prevention:** Keep checks independent, use short but realistic timeouts, avoid shared mutable data, and separate environment outages from product failures when possible.
- **TDD first failing test:** Create one failing availability or critical path check for the capability that must exist after the change.
- **Use existing project tools first:** Prefer existing health checks, deployment probes, monitoring scripts, and CI smoke commands before writing a new harness.

## Regression

- **When to use:** Use a regression test when a known bug, incident, or review finding must remain fixed.
- **What to verify:** Verify the exact observable behavior that failed before, including the boundary condition or scenario that reproduced the defect.
- **What to avoid:** Avoid copying the entire old failure setup if only one condition matters, and avoid assertions that merely encode the implementation fix.
- **Test code structure:** Name the previously broken scenario, arrange only the necessary inputs, act through the public path, and assert the corrected outcome.
- **Assertion standard:** Assert the user-visible, API-visible, or domain-visible symptom that proves the bug cannot reappear unnoticed.
- **Fixture, mock, stub, fake use:** Start with inline reproduction data, extract a fixture only when the same bug setup repeats, use real collaborators from the failing path, use fakes or stubs only for external conditions needed to reproduce the bug, and mock only if the regression was an incorrect outbound interaction.
- **Flaky test prevention:** Remove accidental timing, ordering, and shared-state assumptions from the reproduction so the test fails only for the regression.
- **TDD first failing test:** Reproduce the bug with the smallest failing case before changing implementation.
- **Use existing project tools first:** Put the regression in the nearest existing test layer and use the project's established issue, case naming, and assertion conventions.

## Characterization

- **When to use:** Use a characterization test when existing behavior must be documented before refactoring, migrating, or replacing code whose intended behavior is uncertain.
- **What to verify:** Verify current observable behavior, important edge cases, legacy quirks, and externally relied-on outputs without judging whether they are ideal.
- **What to avoid:** Avoid asserting private implementation details, broad snapshots with no review value, and changing behavior while writing the characterization.
- **Test code structure:** Capture small representative examples around public entry points, then mark known quirks clearly in test names or assertion messages.
- **Assertion standard:** Assert exact current outcomes where compatibility matters and use focused assertions that future refactors can understand.
- **Fixture, mock, stub, fake use:** Prefer inline examples and real legacy objects so current behavior is captured faithfully, use fixtures only to name repeated legacy state, use fakes for unavailable local infrastructure, use stubs for fixed external answers, and avoid mocks unless the legacy behavior is a required outbound call.
- **Flaky test prevention:** Freeze nondeterministic inputs, isolate legacy global state, and avoid depending on production data or ambient environment configuration.
- **TDD first failing test:** If the expected current behavior is not yet captured, write a failing characterization around one public behavior before refactoring.
- **Use existing project tools first:** Use the existing test runner and legacy test helpers closest to the code so the characterization fits the current maintenance workflow.

## Property-based

- **When to use:** Use a property-based test when a behavior should satisfy general invariants across many generated inputs.
- **What to verify:** Verify algebraic properties, round trips, ordering rules, parser invariants, idempotency, validation guarantees, or state machine transitions.
- **What to avoid:** Avoid replacing clear example tests, generating invalid domains accidentally, or asserting vague properties that do not encode a real requirement.
- **Test code structure:** Define the invariant, constrain generators to meaningful inputs, include shrinking support when available, and keep each property focused.
- **Assertion standard:** Assert the invariant for every generated case and include one or two example tests for high-value edge cases.
- **Fixture, mock, stub, fake use:** Generate minimal domain values directly or through existing generators, avoid broad fixtures that hide the property, use fakes for deterministic model implementations, use stubs for fixed external edge responses, and avoid mocks unless the property is explicitly about emitted interactions.
- **Flaky test prevention:** Control seeds when the project records them, bound generated sizes and runtime, avoid time or concurrency races, and persist counterexamples when the tool supports it.
- **TDD first failing test:** Start with one invariant that the current implementation violates, ideally with a concrete counterexample before broadening generation.
- **Use existing project tools first:** Use existing property-testing libraries, generators, seed recording conventions, and CI limits already accepted by the project.

## Snapshot/Golden

- **When to use:** Use a snapshot or golden test when a stable structured output, rendered artifact, generated file, or protocol transcript must be reviewed for unintended changes.
- **What to verify:** Verify meaningful serialized content, layout output, compiler output, generated configuration, or externally consumed artifacts.
- **What to avoid:** Avoid snapshots for noisy data, implementation internals, broad UI trees, random ordering, or changes nobody will review.
- **Test code structure:** Generate the artifact deterministically, normalize irrelevant fields, compare to the approved baseline, and make review intent clear.
- **Assertion standard:** Assert exact output only after removing nondeterministic values and keeping the golden file small enough for human review.
- **Fixture, mock, stub, fake use:** Prefer inline minimal inputs with real serializers or renderers, use fixtures only for named baseline inputs, use fakes for local asset stores, use stubs for fixed external asset responses, and avoid mocks because golden tests should usually verify output rather than calls.
- **Flaky test prevention:** Sort collections, freeze time and locale, normalize paths and generated IDs, and avoid environment-specific formatting.
- **TDD first failing test:** Add or update the smallest golden case that exposes the missing output difference, then review the diff before accepting it.
- **Use existing project tools first:** Use the project's snapshot update workflow, approval review process, serializer options, and formatting tools before adding new golden infrastructure.

## Performance/Benchmark

- **When to use:** Use a performance or benchmark test when latency, throughput, memory, allocation, startup time, or scalability is an explicit requirement or regression risk.
- **What to verify:** Verify measured behavior against a stated budget, baseline, trend, or complexity expectation under a controlled workload.
- **What to avoid:** Avoid arbitrary thresholds, microbenchmarks unrelated to user impact, noisy shared environments, and mixing correctness assertions with unstable timing claims.
- **Test code structure:** Define the workload, warmup, measurement method, environment assumptions, and pass criteria separately from setup.
- **Assertion standard:** Assert against documented budgets or statistically meaningful regressions, and report measurements with enough context to interpret failures.
- **Fixture, mock, stub, fake use:** Use realistic minimal data sets and narrow workload fixtures, use fakes only when they preserve the performance characteristic being measured, use stubs for fixed external latency or responses outside the measurement, and avoid mocks unless measuring a required outbound call count.
- **Flaky test prevention:** Isolate resources, control concurrency, pin representative data, separate benchmark jobs from ordinary unit tests when needed, and account for CI variance.
- **TDD first failing test:** Write a failing benchmark or budget check for the behavior that must improve, such as exceeding the accepted p95 latency or memory limit.
- **Use existing project tools first:** Use the repository's benchmark runner, profiling scripts, performance budgets, and CI reporting before introducing a new measurement stack.

## Security

- **When to use:** Use a security test when a change affects authorization, authentication, input validation, cryptography, secrets, isolation, dependency boundaries, or abuse resistance.
- **What to verify:** Verify access controls, rejected malicious input, safe defaults, audit-relevant behavior, secret handling, and known vulnerability regression cases.
- **What to avoid:** Avoid proving security through happy paths only, leaking secrets in fixtures or logs, relying on obscurity, or disabling protections to make tests pass.
- **Test code structure:** Model the attacker-relevant precondition, perform the operation through a public boundary, and assert denial, sanitization, isolation, or safe failure.
- **Assertion standard:** Assert explicit security outcomes such as forbidden access, escaped output, unchanged protected state, redacted logs, or rejected payloads.
- **Fixture, mock, stub, fake use:** Use neutral inline credentials and real authorization models when possible, use fakes for local identity or permission stores that enforce rules, use stubs for fixed identity-provider claims or error responses, and use mocks only to verify mandatory audit, alerting, or revocation calls.
- **Flaky test prevention:** Isolate tenants and users, reset permissions, avoid shared secrets, control token expiry, and keep time-sensitive claims deterministic.
- **TDD first failing test:** Start with one exploit or policy violation that currently succeeds but must be rejected after the fix.
- **Use existing project tools first:** Prefer existing security test helpers, authorization factories, scanner configuration, and threat-model conventions before adding a new security harness.

## Accessibility

- **When to use:** Use an accessibility test when behavior affects perceivable, operable, understandable, or robust interaction for users with assistive technology or accessibility needs.
- **What to verify:** Verify semantic structure, names and roles, keyboard operation, focus management, contrast-relevant states, error messages, and assistive technology signals supported by the project tools.
- **What to avoid:** Avoid claiming full accessibility conformance from automated checks alone, testing only visual appearance, or asserting implementation-specific markup with no user impact.
- **Test code structure:** Exercise the interaction through accessible roles, keyboard or public controls, then combine automated checks with focused manual or semantic assertions where needed.
- **Assertion standard:** Assert user-observable accessibility outcomes such as reachable controls, correct accessible names, stable focus, announced errors, and absence of tool-detected violations.
- **Fixture, mock, stub, fake use:** Use realistic minimal content and real rendered components, extract fixtures only for repeated accessibility contexts, use fakes for media or platform services that behave locally, use stubs for fixed preference or assistive responses, and avoid mocks unless verifying a required announcement or focus-management callback.
- **Flaky test prevention:** Disable or wait for animations, assert after focus settles, avoid viewport-specific assumptions unless the requirement is viewport-specific, and keep generated IDs deterministic.
- **TDD first failing test:** Write one failing accessibility behavior, such as a keyboard user being unable to reach or activate a required control.
- **Use existing project tools first:** Use existing semantic query helpers, accessibility linters, browser checks, and manual review conventions before adding another accessibility tool.

## Migration/Schema

- **When to use:** Use a migration or schema test when database, data format, API schema, configuration schema, or backward-compatibility changes could break existing data or clients.
- **What to verify:** Verify upgrade and rollback paths, schema constraints, data transformation, defaults, indexes, compatibility, and failure behavior for invalid or legacy data.
- **What to avoid:** Avoid testing only an empty schema, relying on production data, skipping destructive edge cases, or asserting implementation details of the migration tool.
- **Test code structure:** Build the smallest representative old state, run the migration or schema validation through the real project path, and assert the new state.
- **Assertion standard:** Assert preserved data, transformed fields, constraints, indexes, validation errors, and idempotency where the project requires it.
- **Fixture, mock, stub, fake use:** Use minimal inline seed records first, extract fixtures only for repeated legacy states, use fakes such as local databases only when they enforce relevant schema behavior, use stubs for fixed external schema registry responses, and avoid mocks unless verifying a required migration callback.
- **Flaky test prevention:** Use isolated schemas or files, reset migration versions, avoid shared databases, sort introspection output, and clean up generated artifacts deterministically.
- **TDD first failing test:** Create one failing migration case for the legacy state that must be supported before writing or changing the migration.
- **Use existing project tools first:** Use the project's migration runner, schema validator, seed tooling, and rollback conventions before adding custom migration scripts.

## Infrastructure/IaC validation

- **When to use:** Use an infrastructure or IaC validation test when infrastructure definitions, deployment configuration, policies, permissions, networking, or runtime settings can be checked before deployment.
- **What to verify:** Verify generated plans, policy constraints, required resources, least-privilege permissions, environment variables, networking rules, and deployment invariants.
- **What to avoid:** Avoid applying real infrastructure in ordinary tests, hardcoding environment-specific secrets, asserting provider internals, or treating formatting as validation.
- **Test code structure:** Render or plan the infrastructure in an isolated workspace, inspect the resulting configuration or policy output, and assert required invariants.
- **Assertion standard:** Assert specific resources, permissions, security settings, dependencies, and forbidden changes with clear diagnostics.
- **Fixture, mock, stub, fake use:** Use minimal configuration inputs and real IaC parsers or planners in dry-run mode, use fakes for local state backends, use stubs for fixed cloud inventory or policy responses, and use mocks only when the requirement is to verify a deployment orchestrator's outbound provider call.
- **Flaky test prevention:** Pin provider versions where the project does, avoid live cloud state, isolate workspaces and state files, normalize generated ordering, and keep credentials out of test output.
- **TDD first failing test:** Add one failing plan or policy assertion for the infrastructure invariant the change must enforce.
- **Use existing project tools first:** Use existing IaC validation commands, policy engines, plan reviewers, and CI gates before adding a new infrastructure validation tool.
