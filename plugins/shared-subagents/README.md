# Shared Subagents

Shared Codex subagent templates for reusable Superpowers workflows across multiple machines and projects.

## Cross-Check Summary

- Real `packages/awesome-codex-subagents` TOML files use `developer_instructions`.
- Real TOML files declare `model`, `model_reasoning_effort`, and `sandbox_mode` per role.
- Discovery, documentation verification, and context packaging roles usually use `gpt-5.3-codex-spark` with `medium` reasoning.
- Review, security, and architectural judgment roles usually use `gpt-5.4` with `high` reasoning.
- `packages/awesome-codex-skills` separates `SKILL.md` frontmatter from execution guidance.
- See `references/awesome-agent-style-benchmark.md` for structure and length observations.

## Installation

```bash
rtk python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --dry-run
rtk python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --backup
```

## Principles

- Install only project-agnostic agents globally.
- Keep stack-specific agents in each project's `.codex/agents/` directory.
- Do not modify the Superpowers plugin cache during installation.
- Print AGENTS.md guidance for copy-paste instead of editing repository files.
- Keep MCP server configuration outside this plugin.

## MCP inheritance

Codex custom agents inherit parent session settings when agent TOML files omit those keys. In practice, global MCP servers configured in `~/.codex/config.toml` may be started for spawned subagents, which can add startup latency or expose failures from unrelated MCP servers.

shared-subagents does not install or modify MCP servers. Keep MCP server configuration in `~/.codex/config.toml` or project `.codex/config.toml`, and tune slow or optional servers there with settings such as `startup_timeout_sec`, `tool_timeout_sec`, `required = false`, or `enabled = false`.

Do not add one-off MCP server blocks to these shared agent templates unless the agent truly owns that tool surface. Prefer user or project Codex config for machine-specific MCP choices.

## Superpowers Integration

Use `references/superpowers-routing.md` for Superpowers stage routing and custom-agent fallback rules.

## Skill Integration

Use `$shared-subagents:scaffold` to ask Codex to run the install, AGENTS.md block, and verification workflow.

## Verification

```bash
rtk python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --dry-run
rtk python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --print-agents-md-block
rtk python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --codex-home temps/2026-05-05/shared-subagents/codex-home
rtk find temps/2026-05-05/shared-subagents/codex-home/agents -maxdepth 1 -type f
```

Expected results:

- Dry run prints eight target installation paths.
- The AGENTS.md block command prints copy-paste Markdown and does not edit files.
- The temporary Codex home contains eight TOML files.
- Each TOML file contains `developer_instructions`.
- Real Codex home installation should use `--backup` unless the operator intentionally chooses `--force`.

After installing into the real `~/.codex/agents/` directory, restart Codex and manually verify whether custom agent names can be invoked.
