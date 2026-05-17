---
name: install
description: Use when installing shared-subagents Codex TOML subagents into a real project-local .codex/agents directory.
---

# Install Shared Subagents

Install the bundled Codex TOML subagents into a real project's repository-root `.codex/agents/` directory.

## Commands

Preview targets from the current project root:

```bash
python3 /path/to/shared-subagents/skills/install/install.py --dry-run
```

Install with backups for existing files:

```bash
python3 /path/to/shared-subagents/skills/install/install.py --install --backup --project-root .
```

Use `--force` only when replacing existing project-local copies is intentional.

## Rules

- Install only Codex TOML agent files into `.codex/agents/`.
- Do not edit `AGENTS.md`, `CLAUDE.md`, or MCP configuration.
- Do not install into nested monorepo package directories unless the user explicitly chooses that project root.
- Refuse to overwrite existing files unless `--backup` or `--force` is provided.
- After installation, ask the user to restart Codex before expecting newly copied agents to appear.

## Report

After running, report:

- project root used
- files that would be installed or were installed
- whether any backups were created
- whether Codex restart remains required
