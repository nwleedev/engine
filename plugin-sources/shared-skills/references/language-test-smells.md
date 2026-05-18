# Language Test Smells

Use this reference with `test-assertion-quality.md` when a downstream
application project needs stack-aware test review. These examples do not
replace project conventions; they help identify common ways tests become
implementation-detail checks, weak assertions, mock-only checks, or flaky
shared-state checks.

## Common Smell Map

| stack | smell_pattern | blocking_smell_code | preferred_assertion_strategy |
| --- | --- | --- | --- |
| JavaScript/TypeScript | Enzyme-style component instance access, private hook state, CSS class assertions, whole-tree snapshots, `expect(fn).not.toThrow()`, `toBeTruthy()`, or only `expect(mock).toHaveBeenCalled()`. | implementation_detail_assertion, broad_snapshot, private_behavior_test, weak_assertion, mock_only_assertion, coverage_theater | Prefer Testing Library-style queries by role, label, text, or visible result for UI, and assert exact return values, persisted state, emitted events, normalized errors, or explicit outbound contract payloads for services. |
| Python | Tests call underscored helpers directly, monkeypatch internals, or assert only that a fixture object exists. | private_behavior_test, implementation_detail_assertion, weak_assertion | Exercise public functions, commands, routes, or domain services and assert exact output, error, state transition, or file content. |
| Java/Kotlin | Mockito interaction tests replace domain behavior or verify call order with no observable result. | mock_only_assertion, implementation_detail_assertion | Prefer public service/API results, state changes, repository-visible effects, or contract payload assertions. |
| .NET | Moq or substitute interaction tests verify service calls without asserting public output, or tests assert only that an exception was not thrown. | mock_only_assertion, weak_assertion, non_diagnostic_failure | Assert public API responses, domain results, persisted state, emitted messages, typed errors, or policy outcomes with xUnit, NUnit, MSTest, or project-standard helpers. |
| Go | Table tests omit expected values, use shared package globals, or only check error is nil. | weak_assertion, flaky_shared_state | Assert concrete outputs and reset per-test state; use `t.Run` cases with explicit names and isolated fixtures. |
| Rust | Unit tests reach private modules for behavior that has a public API, or use broad insta snapshots without reviewed scope. | private_behavior_test, broad_snapshot | Assert public API results, error variants, serialized forms, or focused reviewed snapshots with deterministic inputs. |
| SQL/Migration | Tests count rows only, depend on ambient seed data, or accept generated expected output without review. | weak_assertion, flaky_shared_state, coverage_theater | Assert specific rows, constraints, transformations, migration idempotency, rollback behavior, and drift-reviewed generated expected output. |
| Browser or E2E | Tests sleep, depend on order, assert selectors or CSS classes, or cover every unit path through the browser. | flaky_shared_state, implementation_detail_assertion, wrong_layer | Drive public user flows with stable readiness signals and assert visible or persisted outcomes at the right layer. |
| IaC | Tests snapshot whole plans, ignore provider noise, or assert formatting instead of policy invariants. | broad_snapshot, non_diagnostic_failure, coverage_theater | Assert explicit resources, permissions, security settings, generated policy fields, or forbidden changes. |

## Review Checklist

- Confirm the test names the `behavior_boundary`, `public_entrypoint`, and
  `observable_result` for the downstream application project.
- Confirm the `assertion_strategy` can fail for the current acceptance
  criterion and produces a diagnostic failure.
- Confirm `fixture_mock_policy` explains every mock, fake, stub, fixture,
  snapshot, seed, cassette, generated expected output, schema example,
  benchmark baseline, or IaC expected output.
- Confirm `determinism_policy` controls time, randomness, ordering, locale,
  filesystem, ports, generated IDs, concurrency, and shared mutable state.
- Confirm `test_smell_risk` lists `none` or one or more blocking smell codes:
  `weak_assertion`, `mock_only_assertion`, `private_behavior_test`,
  `implementation_detail_assertion`, `broad_snapshot`,
  `non_diagnostic_failure`, `wrong_layer`, `flaky_shared_state`, or
  `coverage_theater`.
