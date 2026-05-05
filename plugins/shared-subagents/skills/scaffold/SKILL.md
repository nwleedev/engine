---
name: scaffold
description: Use when installing or verifying the shared Codex subagent templates, printing the AGENTS.md guidance block, or setting up shared subagents across machines and projects.
---

# Shared Subagents Scaffold

Install and verify shared Codex subagent templates without editing repository files automatically.

## Run

From the skill directory path shown by Codex:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --dry-run
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --print-agents-md-block
```

To install into the real Codex home:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --backup
```

To verify safely before touching the real Codex home:

```bash
python3 /path/to/shared-subagents/skills/scaffold/scaffold.py --install --codex-home temps/2026-05-05/shared-subagents/codex-home
find temps/2026-05-05/shared-subagents/codex-home/agents -maxdepth 1 -type f
```

## Behavior

- Copies eight bundled custom agent TOML files into a Codex `agents/` directory.
- Refuses to overwrite existing files unless `--backup` or `--force` is used.
- Prints an AGENTS.md guidance block for copy-paste.
- Does not modify AGENTS.md automatically.
- Does not modify the Superpowers plugin cache.
- Does not install, remove, or edit MCP server configuration.
- Requires Codex restart before newly installed global agents are expected to appear.

## MCP Notes

Codex custom agents may inherit MCP servers from the parent session. If subagent startup is slow or noisy, inspect `~/.codex/config.toml` and tune MCP servers there with `startup_timeout_sec`, `tool_timeout_sec`, `required = false`, or `enabled = false`.

Do not patch bundled shared agents with machine-specific MCP settings. MCP choices belong in user or project Codex config.

## User-visible Output

After running commands, report:

- dry-run target paths
- whether the AGENTS.md block printed successfully
- whether eight TOML files exist in the target `agents/` directory
- whether manual Codex restart and custom agent invocation verification remain
- whether MCP startup tuning remains a separate user config task

If installing into the real `~/.codex/agents/` directory, prefer `--backup` so existing files with the same names are preserved before replacement.
