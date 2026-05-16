# Shared Skills

Shared Codex and Claude Code skills for traceable requirements, evidence-backed planning, deep research artifacts, downstream scenario-based test writing, and completion gates.

## Purpose

`shared-skills` packages main-session workflow skills that produce explicit artifacts instead of loose advice. Use it to trace user requests from requirements through specs, plans, implementation evidence, research evidence, scenario tests, and final verification gates.

`shared-subagents` remains the plugin for delegated specialist review or research. This plugin keeps the main session responsible for artifact shape, traceability, and completion evidence.

## Breaking redesign

Earlier advisory routes are intentionally removed from active source and
generated artifacts. Migration mapping belongs in public migration docs, not in
generated skill descriptions.

## Plugin-only distribution

This plugin exposes skills through generated Codex and Claude plugin manifests and harness-specific plugin paths.

It does not copy skills into a user home directory, does not edit AGENTS.md, does not install MCP servers, and does not create a scaffold command.

After installing the plugin, restart the host coding agent or tool if the new skills do not appear. Invoke skills explicitly with `$shared-skills:<skill-name>` or describe the task naturally and let the host tool match the skill description.

## Included skills

- `requirements-packet`: convert user requests into confirmed requirements, inferred assumptions, open questions, non-goals, and acceptance criteria.
- `spec-contract`: turn confirmed requirements into behavior, interface, failure-mode, and compatibility contracts.
- `plan-contract`: create implementation plans with linked requirements, target artifacts, validation methods, and fallbacks.
- `implementation-evidence`: record files changed, behavior changed, commands run, and linked requirement/task evidence.
- `verification-gate`: gate completion claims with required evidence, failed items, not-run items, residual risks, and final status.
- `research-plan`: define research questions, source strategies, counterevidence strategies, and stop conditions.
- `source-ledger`: track source authority, recency, supported claims, and limitations.
- `claim-evidence-map`: map claims to source IDs, confidence, counterevidence, and decision impact.
- `scenario-test-designer`: link acceptance criteria to user scenarios, happy paths, boundary scenarios, and failure scenarios.
- `test-plan-contract`: map scenarios to test layers, files, commands, fixture/mock policy, and evidence IDs.
- `tdd-test-writing`: write tests through a TDD workflow, choose test types by behavior boundary, and prepare reviewer handoff evidence.
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
