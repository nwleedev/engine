# Common Subagents

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
rtk python3 plugins/common-subagents/scripts/install_common_subagents.py --dry-run
rtk python3 plugins/common-subagents/scripts/install_common_subagents.py
```

## Principles

- Install only project-agnostic agents globally.
- Keep stack-specific agents in each project's `.codex/agents/` directory.
- Do not modify the Superpowers plugin cache during installation.
- Print AGENTS.md guidance for copy-paste instead of editing repository files.

## Superpowers Integration

Use `references/superpowers-routing.md` for Superpowers stage routing and custom-agent fallback rules.

## Verification

```bash
rtk python3 plugins/common-subagents/scripts/install_common_subagents.py --dry-run
rtk python3 plugins/common-subagents/scripts/print_agents_md_block.py
rtk python3 plugins/common-subagents/scripts/install_common_subagents.py --codex-home temps/2026-05-05/common-subagents/codex-home
rtk find temps/2026-05-05/common-subagents/codex-home/agents -maxdepth 1 -type f
```

Expected results:

- Dry run prints eight target installation paths.
- The AGENTS.md block command prints copy-paste Markdown and does not edit files.
- The temporary Codex home contains eight TOML files.
- Each TOML file contains `developer_instructions`.

After installing into the real `~/.codex/agents/` directory, restart Codex and manually verify whether custom agent names can be invoked.
