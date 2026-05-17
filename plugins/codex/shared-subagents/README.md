<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-subagents/README.md -->

# Shared Subagents

Shared Codex and Claude Code subagent templates for reusable Superpowers workflows across projects.

## Agent Roles

- `context-manager`, `code-mapper`, and `docs-researcher` gather project context, code structure, and official documentation evidence.
- `source-researcher`, `requirements-reviewer`, `plan-reviewer`, and `citation-verifier` keep Source Ledger, Requirement Packet, Plan Contract, Traceability Matrix, and Claim Evidence Map work separate.
- `test-adequacy-reviewer`, `closure-reviewer`, and `risk-reviewer` review downstream test quality, verification-gate evidence, risk register items, residual risk, rollback, fallback, and unverifiable items.
- `reviewer`, `code-reviewer`, and `security-auditor` remain separate gates for correctness/behavior regression/contract review, maintainability/design/readability, and security-audit review.

## Cross-Check Summary

- Real `packages/awesome-codex-subagents` TOML files use `developer_instructions`.
- Real TOML files declare `model`, `model_reasoning_effort`, and `sandbox_mode` per role.
- Discovery, documentation verification, and context packaging roles usually use `gpt-5.3-codex-spark` with `medium` reasoning.
- Review, security, and architectural judgment roles usually use `gpt-5.4` with `high` reasoning.
- `packages/awesome-codex-skills` separates `SKILL.md` frontmatter from execution guidance.
- See `references/awesome-agent-style-benchmark.md` for structure and length observations.

## Installation

### Using In Codex

This bundle ships generated Codex TOML agents under `agents/`.

Use the bundled agents through the runtime plugin loader when available. If your Codex environment requires project-local agents, copy the needed TOML files into the repository root `.codex/agents/` directory and restart Codex.

Use `AGENTS.block.md` as the committed copy-paste block for durable routing guidance in project `AGENTS.md` files. The block is not only an agent list. It also sets shared-skills workflow routing: requirements go through `requirements-packet`, implementation plans through `spec-contract` and `plan-contract`, behavior-changing work through the scenario/test/TDD skills, changed work through `implementation-evidence`, and completion claims through `verification-gate`.

### Using In Claude Code

This bundle ships generated Markdown subagents under `agents/`. Claude Code plugin-bundled agents are Markdown files with YAML frontmatter and can be discovered from the plugin `agents/` directory at startup. If your Claude Code environment discovers plugin-bundled agents directly, invoke them by name. If your environment requires project-local agents, copy the needed files into `.claude/agents/` and restart Claude Code.

Example: `Use the test-adequacy-reviewer subagent to review tests for AC-001 / SCN-001.`

## Principles

- Keep shared agents bundled with the plugin whenever the runtime can discover plugin-bundled agents.
- If local copies are required, keep them at the repository root runtime directory, not inside nested monorepo packages.
- Keep stack-specific or organization-private agents in project-local runtime directories.
- Keep `AGENTS.block.md` as the durable project policy source for when shared-skills and shared-subagents must be used.
- Do not add scaffold skills, copy-install commands, or AGENTS.md editing behavior to this plugin.
- Keep MCP server configuration outside this plugin.

## MCP inheritance

Codex custom agents inherit parent session settings when agent TOML files omit those keys. In practice, MCP servers configured in user or project Codex config may be started for spawned subagents, which can add startup latency or expose failures from unrelated MCP servers.

shared-subagents does not install or modify MCP servers. Keep MCP server configuration in `~/.codex/config.toml` or project `.codex/config.toml`, and tune slow or optional servers there with settings such as `startup_timeout_sec`, `tool_timeout_sec`, `required = false`, or `enabled = false`.

Do not add one-off MCP server blocks to these shared agent templates unless the agent truly owns that tool surface. Prefer user or project Codex config for machine-specific MCP choices.

## Superpowers Integration

Use `references/superpowers-routing.md` for Superpowers stage routing and custom-agent fallback rules.

## Verification

Expected generated bundle results:

- `AGENTS.block.md` exists at the plugin root and contains `SHARED-SUBAGENTS` markers.
- The Codex bundle contains thirteen TOML files under `agents/`.
- The Claude Code bundle contains thirteen Markdown files under `agents/`.
- Each TOML file contains `developer_instructions`.
- Each TOML file contains `# shared-subagents:provided-agent` so optional project-local copies can be identified as plugin-provided templates.
- The Codex manifest does not advertise `skills`, because this plugin is agent-only.
