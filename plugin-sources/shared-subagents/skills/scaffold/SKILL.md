---
name: scaffold
description: Use when installing or verifying project-local shared Codex subagent templates, printing the AGENTS.md guidance block, or setting up shared skill/subagent workflow guidance across projects.
---

# Shared Subagents Scaffold

Install and verify shared Codex subagent templates in a project's `.codex/agents` directory and print AGENTS.md guidance for shared-skills and shared-subagents without editing AGENTS.md automatically.

## Run

From the skill directory path shown by Codex:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --dry-run
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --print-agents-md-block
```

To install into the current project's `.codex/agents` directory:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --backup --project-root .
```

To verify safely before touching the current project:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --project-root temps/2026-05-05/shared-subagents/project-root
find temps/2026-05-05/shared-subagents/project-root/.codex/agents -maxdepth 1 -type f
```

## Behavior

- Copies thirteen bundled custom agent TOML files into a project-local `.codex/agents/` directory.
- Refuses to overwrite existing files unless `--backup` or `--force` is used.
- Prints an AGENTS.md guidance block for copy-paste, including shared-skills workflow routing and shared-subagents delegation routing.
- Does not modify AGENTS.md automatically.
- Does not modify the Superpowers plugin cache.
- Does not install, remove, or edit MCP server configuration.
- Requires Codex restart before newly installed project-local agents are expected to appear.

## MCP Notes

Codex custom agents may inherit MCP servers from the parent session. If subagent startup is slow or noisy, inspect project `.codex/config.toml` or user `~/.codex/config.toml` and tune MCP servers there with `startup_timeout_sec`, `tool_timeout_sec`, `required = false`, or `enabled = false`.

Do not patch bundled shared agents with machine-specific MCP settings. MCP choices belong in user or project Codex config.

## User-visible Output

After running commands, report:

- dry-run target paths
- whether the AGENTS.md block printed successfully
- whether the AGENTS.md block includes shared-skills workflow routing and shared-subagents delegation routing
- whether thirteen TOML files exist in the target `.codex/agents/` directory
- whether manual Codex restart and custom agent invocation verification remain
- whether MCP startup tuning remains a separate user config task
