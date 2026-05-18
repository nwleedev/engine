# Test Assertion Quality

Use this reference when downstream application project tests must prove current
requirements through observable behavior instead of implementation details. The
goal is not to increase line coverage or prove that code executed; the goal is
diagnostic confidence that an application behavior, public contract, generated
artifact, security policy, performance budget, or infrastructure invariant still
holds.

## Behavior Boundary Classification

Classify the behavior boundary before choosing assertions. Record the
`behavior_boundary`, `public_entrypoint`, and `observable_result` in the test
plan so reviewers can see what the downstream project exposes to users,
callers, operators, external systems, or public artifacts.

| behavior_boundary | public_entrypoint | observable_result | hidden_implementation_details_to_avoid | required_test_layer | why_this_layer_is_narrowest_reliable_layer |
| --- | --- | --- | --- | --- | --- |
| domain_rule | public function, service method, command handler, or policy object | returned value, validation error, state transition, or emitted domain event | private helper names, incidental branch order, or internal cache state | unit or component | This is the narrowest public boundary that can fail for the rule. |
| public_api | HTTP route, RPC method, CLI command, SDK method, or message consumer | status, payload, error body, persisted side effect, or emitted event | controller internals, middleware call order, or non-contract fields | contract or integration | The public entrypoint exposes the caller-visible contract and side effects. |
| ui_behavior | rendered component, page, flow, or accessibility interaction | visible text, role, accessible name, navigation, focus, or submitted result | component instance state, CSS class names, or framework internals | component or end-to-end | The selected layer observes the behavior the user can see or operate. |
| integration_boundary | repository, adapter, serializer, queue, filesystem, database, or local service | data crossing the boundary, transaction result, durable write, or normalized error | private adapter methods or incidental serialization order | integration | The boundary result is only trustworthy when the local integration path runs. |
| generated_artifact_contract | snapshot, golden, generated config, schema example, benchmark baseline, or IaC expected output | deterministic artifact diff or schema-compatible output | broad noisy snapshots or generator implementation details | artifact or contract | The artifact itself is the public contract and must be reviewed narrowly. |
| security_policy | auth, input validation, tenant isolation, redaction, cryptography, or abuse boundary | denial, sanitization, isolation, redaction, audit result, or safe failure | internal guard names or mock-only policy calls | security or integration | The layer must prove the externally meaningful protection outcome. |
| performance_budget | startup, latency, memory, throughput, allocation, or complexity budget | measured value against a documented budget or baseline | incidental timing on uncontrolled hardware or implementation counters | benchmark or performance | The measurement boundary is the smallest controlled budget surface. |

## Assertion Quality Gate

A test may count as core downstream application coverage only when every row has
an `assertion_strategy`, `fixture_mock_policy`, `determinism_policy`, and
`test_smell_risk`. The assertion must fail when the linked requirement breaks,
and the failure should identify the broken contract or behavior.

| quality_id | required_check | blocking_smell_code | pass_standard |
| --- | --- | --- | --- |
| AQ-001 | Assertion proves a user, caller, operator, external system, or public artifact can observe the result. | implementation_detail_assertion | The assertion targets public output, state, error, event, permission, artifact, or invariant. |
| AQ-002 | Assertion is specific enough to fail for the linked requirement. | weak_assertion | The assertion names expected values, structures, errors, transitions, policies, or budgets. |
| AQ-003 | Mock assertions are not the only proof unless the outbound interaction contract is the requirement. | mock_only_assertion | A visible result is asserted, or the outbound call contract is the explicit behavior boundary. |
| AQ-004 | Snapshot or golden assertions are narrow, deterministic, and reviewed. | broad_snapshot | The baseline is small, noise-normalized, and tied to a public artifact contract. |
| AQ-005 | Failure output is diagnostic. | non_diagnostic_failure | Failure identifies the scenario, acceptance criterion, expected result, and observed result. |
| AQ-006 | Test layer matches the behavior boundary. | wrong_layer | The selected layer is the narrowest reliable layer that can fail for the behavior. |
| AQ-007 | Determinism is controlled. | flaky_shared_state | Time, randomness, ordering, shared state, ports, locale, generated IDs, and concurrency are isolated or fixed. |
| AQ-008 | Coverage claim proves behavior, not activity. | coverage_theater | The test can fail for a real requirement regression, not only for code execution or coverage metrics. |

## Blocking Smell Codes

Treat these smell codes as blocking findings until the test is rewritten,
demoted, or excluded from core evidence:

- `weak_assertion`: truthy, not-null, no-throw, called-once, or existence-only assertion that can pass when the requirement is broken.
- `mock_only_assertion`: verifies only calls to a mock while the user-visible or boundary-visible result is unasserted.
- `private_behavior_test`: calls private methods, private classes, framework internals, or internal state as the behavior under test.
- `implementation_detail_assertion`: asserts incidental call order, CSS classes, component internals, database implementation details, or non-contract fields.
- `broad_snapshot`: approves a large or noisy snapshot without a public artifact contract, review scope, or deterministic normalization.
- `non_diagnostic_failure`: fails with a vague message that does not reveal which requirement, contract, input, or expected result broke.
- `wrong_layer`: uses a broader or narrower layer that hides the behavior boundary or misses the public entrypoint.
- `flaky_shared_state`: depends on shared mutable state, uncontrolled time, random values, test order, real services, ambient data, or sleeps.
- `coverage_theater`: exists mainly to increase coverage numbers, execute lines, or satisfy a mock rather than prove current behavior.

## TDD Quality Evidence

TDD evidence for downstream application projects must include the behavior
quality row, not only red/green commands.

| evidence_id | behavior_boundary | public_entrypoint | observable_result | intended_failure_reason | why_failure_proves_missing_behavior | assertion_quality_gate | determinism_controls | fixture_mock_justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TQE-001 | public_api |  |  |  |  |  |  |  |

Use `test_smell_risk` value `none` only after checking all blocking smell codes.
When a smell remains, route the row to `test-adequacy-reviewer` and do not count
the test as core completion evidence until the blocking code is resolved.
