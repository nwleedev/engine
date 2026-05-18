<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/README.md -->

# Shared Skills

Shared Codex and Claude Code skills for traceable requirements, evidence-backed planning, deep research artifacts, downstream scenario-based test writing, and completion gates.

## Purpose

`shared-skills` packages main-session workflow skills that produce explicit artifacts instead of loose advice. Use it to trace user requests from requirements through specs, plans, implementation evidence, research evidence, testing workflow routes, scenario tests, and final verification gates.

`shared-subagents` remains the plugin for delegated specialist review or research. This plugin keeps the main session responsible for artifact shape, traceability, and completion evidence.

## Breaking redesign

Earlier advisory routes are intentionally removed from active source and
generated artifacts. Migration mapping belongs in public migration docs, not in
generated skill descriptions.

## Plugin-only distribution

This plugin exposes skills through generated Codex and Claude plugin manifests and harness-specific plugin paths.

It does not copy skills into a user home directory, does not edit AGENTS.md, does not install MCP servers, and does not create a scaffold command.

After installing the plugin, restart the host coding agent or tool if the new skills do not appear. Invoke skills explicitly with `$shared-skills:<skill-name>` or describe the task naturally and let the host tool match the skill description.

## Artifact Map

- `requirements-packet`, `spec-contract`, `plan-contract`, `spec-plan-coverage`, `implementation-evidence`, and `verification-gate` use `references/workflow-artifacts.md`.
- `research-plan`, `source-ledger`, and `claim-evidence-map` use `references/deep-research-pipeline.md`.
- `testing-workflow`, `scenario-test-designer`, `test-suite-reconciliation`, `test-plan-contract`, and `tdd-cycle` use `references/downstream-test-contracts.md`, including the Fixture Governance Contract.
- `test-suite-reconciliation` also uses `references/test-relevance-decisions.md` and `references/test-artifact-drift.md` for existing test decisions and artifact drift review.
- `comment-writing`, `implementation-discipline`, and `debugging-discipline` keep execution scoped and feed evidence into the same workflow artifacts.

## Downstream Test Gate

Start all testing-related work with `testing-workflow` before selecting a downstream testing skill or reviewer. New behavior coverage proceeds through `scenario-test-designer`, `test-plan-contract`, and `tdd-cycle`; review-only work routes to the appropriate reviewer; artifact drift routes to reconciliation; and test-inapplicable work records the reason through `test-plan-contract` and `verification-gate`. Changes to existing requirements, public contracts, schemas, migrations, bug expectations, security policy, performance budgets, generated artifact contracts, or expected artifact baselines require reconciliation before new tests are added.

Core scenario coverage must link to an Acceptance Criteria ID or User Scenario ID, use the nearest executable project test layer, and justify each fixture, fake, stub, or mock against observable behavior. `test-adequacy-reviewer` should review downstream test-writing work before closure when subagents are available.

The default fixture budget is `0`. Any fixture, mock, fake, stub, snapshot, seed record, generated input, or test-only adapter requires a Fixture Governance Contract row with a linked scenario, linked spec clause, real-boundary alternative, drift check, owner, and expiry or update trigger.

## Included skills

- `requirements-packet`: convert user requests into confirmed requirements, inferred assumptions, open questions, non-goals, and acceptance criteria.
- `spec-contract`: turn confirmed requirements into behavior, interface, failure-mode, and compatibility contracts.
- `plan-contract`: create implementation plans with linked requirements, target artifacts, validation methods, and fallbacks.
- `spec-plan-coverage`: extract a Spec Ledger and validate the Spec-to-Plan Coverage Matrix before implementation or completion.
- `implementation-evidence`: record files changed, behavior changed, commands run, and linked requirement/task evidence.
- `verification-gate`: gate completion claims with required evidence, failed items, not-run items, residual risks, and final status.
- `research-plan`: define research questions, source strategies, counterevidence strategies, and stop conditions.
- `source-ledger`: track source authority, recency, supported claims, and limitations.
- `claim-evidence-map`: map claims to source IDs, confidence, counterevidence, and decision impact.
- `testing-workflow`: classify testing requests, output the `Testing Workflow Route`, and route work to the correct downstream testing skill or reviewer.
- `scenario-test-designer`: link acceptance criteria to user scenarios, happy paths, boundary scenarios, and failure scenarios.
- `test-suite-reconciliation`: reconcile existing tests and test artifacts against changed requirements before new tests are added or evidence is accepted.
- `test-plan-contract`: map scenarios to test layers, files, commands, fixture/mock policy, and evidence IDs.
- `tdd-cycle`: write tests through a TDD workflow, choose test types by behavior boundary, and prepare reviewer handoff evidence.
- `comment-writing`: write language/technology-stack-appropriate comments and documentation comments for new-teammate understanding, with `docs-researcher` and `code-reviewer` handoff points.
- `implementation-discipline`: keep code, docs, config, and operational changes scoped and traceable.
- `debugging-discipline`: investigate failures and conflicting evidence before proposing fixes.

## Boundaries

- Use AGENTS.md for durable project rules that should apply to every turn.
- Use shared-skills for repeatable workflow artifacts and domain-independent main-session procedures.
- Use shared-subagents only when work should be delegated to a specialized subagent.
- Keep stack-specific or organization-private skills in repo-local `.agents/skills`.

## Quality rules

- Skills must stay narrow and artifact-focused.
- Descriptions must start with the trigger condition.
- Each skill must support both development work and non-development work.
- Each skill must include output expectations and "Do not" guardrails.
- Do not add copy-install, scaffold, or AGENTS.md editing behavior to this plugin.
