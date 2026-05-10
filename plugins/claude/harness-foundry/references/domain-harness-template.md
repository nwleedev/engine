<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/harness-foundry/references/domain-harness-template.md -->

# <domain> Domain Harness

## Metadata

- domain: `<domain>`
- work_type: `development | non-development | mixed`
- status: `draft | active | deprecated`
- owner: `<team-or-person>`
- last_reviewed: `<YYYY-MM-DD>`

## Purpose

Explain the real repeated work this harness supports and what success looks like.

## Scope

List included repositories, folders, documents, workflows, teams, and user-facing outputs.

## Non-Goals

List tasks this harness must not try to cover.

## Inputs

List project files, docs, external sources, user-provided context, and permissions needed.

## Outputs

List artifacts the AI may create, edit, review, or summarize.

## Components

### Skills

List project-local skills that teach repeatable domain workflows.

### Subagents

List optional subagents only when role separation materially improves the workflow.

### Rules

List durable project rules that should apply across relevant AI sessions.

### Hooks

List optional automation hooks, their trigger points, and the approval needed before activation.

### MCP Guidance

List MCP servers or apps that may help, including authentication and privacy constraints.

### Evals

List scenario-based checks that prove the harness works for normal, failure, and evidence-sensitive paths.

### Guardrails

List explicit constraints for what the AI may not do, what requires approval, and what must be verified.

## Guardrails

Separate development guardrails from non-development guardrails when `work_type` is `mixed`.

## Maintenance

Define owners, review cadence, deprecation rules, and how changes are reflected in `docs/domain-harness/index.md`.
