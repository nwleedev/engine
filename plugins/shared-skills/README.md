# Shared Skills

Shared Codex skills for main-session quality gates across development and non-development work.

## Purpose

`shared-skills` improves the quality of ordinary Codex work without spawning subagents. It packages repeatable quality workflows as skills so Codex can load the right procedure only when it is relevant.

`shared-subagents` remains the plugin for Superpowers workflows that explicitly spawn subagents. This plugin is the complementary no-subagent layer for the main Codex session.

## Plugin-only distribution

This plugin exposes skills through `.codex-plugin/plugin.json`.

It does not copy skills into a user home directory, does not edit AGENTS.md, does not install MCP servers, and does not create a scaffold command.

After installing the plugin, restart Codex if the new skills do not appear. Invoke skills explicitly with `$shared-skills:<skill-name>` or describe the task naturally and let Codex match the skill description.

## Included skills

- `requirements-clarifier`: clarify requirements, scope, non-goals, acceptance criteria, and blocking questions.
- `research-crosscheck`: verify claims and decisions with source-backed research and counterevidence.
- `task-planner`: turn approved requirements or research into a small ordered execution plan.
- `implementation-discipline`: keep code, docs, config, and operational changes scoped and traceable.
- `debugging-discipline`: investigate failures and conflicting evidence before proposing fixes.
- `review-checklist`: review artifacts for correctness, risk, gaps, and actionability.
- `verification-evidence`: gather evidence before completion, correctness, readiness, or decision-ready claims.

## Boundaries

- Use AGENTS.md for durable project rules that should apply to every turn.
- Use shared-skills for repeatable quality workflows and domain-independent procedures.
- Use shared-subagents only when work should be delegated to a specialized subagent.
- Keep stack-specific or organization-private skills in repo-local `.agents/skills`.

## Quality rules

- Skills must stay narrow and procedure-focused.
- Descriptions must start with the trigger condition.
- Each skill must support both development work and non-development work.
- Each skill must include output expectations and "Do not" guardrails.
- Do not add copy-install, scaffold, or AGENTS.md editing behavior to this plugin.
