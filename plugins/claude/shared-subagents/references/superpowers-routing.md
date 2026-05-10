<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-subagents/references/superpowers-routing.md -->

# Superpowers Common Subagent Routing

## Principles

- Use shared custom agent names directly when the runtime supports them.
- When custom agent names are unavailable, inject role instructions into `explorer`, `worker`, or `default`.
- Keep `agents.max_depth = 1`.
- Start with 3-4 concurrent agents unless the task clearly needs more.

## Stage Routing

| Superpowers stage | Preferred agent | Fallback |
|---|---|---|
| brainstorming | `online-researcher`, `spec-reviewer` | `explorer` with online/spec review prompt |
| writing-plans | `context-manager`, `spec-reviewer` | `explorer` with context/spec prompt |
| subagent-driven-development start | `context-manager`, `code-mapper` | `explorer` with mapping prompt |
| API or library verification | `docs-researcher` | `explorer` with docs verification prompt |
| spec compliance review | `spec-reviewer` | `default` with spec-only review prompt |
| correctness review | `reviewer` | `default` with PR review prompt |
| code quality review | `code-reviewer` | `default` with code-health review prompt |
| security review | `security-auditor` | `default` with security review prompt |

## Fallback Prompt Rules

Every fallback prompt must include these constraints.

- Perform exactly one assigned role.
- Read only the files and evidence needed for that role.
- Do not edit code unless the parent explicitly grants write scope.
- Return only findings, evidence, risks, and next action.
- Route out-of-scope questions back to the parent agent.

## Do Not

- Do not use `online-researcher` for API documentation verification.
- Do not use `docs-researcher` for market or strategy judgment.
- Do not use `spec-reviewer` for implementation code-quality review.
- Do not ask `reviewer` and `code-reviewer` the same question in parallel.
- Do not modify the Superpowers plugin cache during installation.
