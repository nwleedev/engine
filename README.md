# engine

engine is a multi-harness plugin monorepo for Codex and Claude Code.

The repository separates plugin source material, shared domain logic,
harness-specific renderers, and generated plugin artifacts. Current generated
outputs are reproducible from tracked source and committed for direct use.

## Repository Layout

| Path | Purpose |
|---|---|
| `plugin-sources/` | Canonical source for marketplace metadata, adapter trees, shared skills, shared subagents, and harness-foundry material. |
| `packages/` | Runtime-agnostic Python domain logic shared by build and validation tools. |
| `renderers/` | Harness renderers that translate canonical source into Codex and Claude Code plugin layouts. |
| `plugins/codex/<plugin>` | Generated Codex plugin artifacts. |
| `plugins/claude/<plugin>` | Generated Claude Code plugin artifacts. |

Do not edit generated plugin artifacts directly when an equivalent source file
exists under `plugin-sources/` or `packages/`. Change that source, update shared
logic in `packages/`, or update harness output rules in `renderers/`, then
regenerate the artifacts.

## Plugin Families

The core plugin families include `session-memory` and `quality-guard`.

The generated multi-harness families include `session-memory`,
`quality-guard`, `shared-skills`, `shared-subagents`, and `harness-foundry`.
`deep-research-prompt-export` is the prompt handoff plugin for exporting
source-backed ChatGPT Deep Research prompts from live project context without
calling external APIs.
`tools/build_plugins.py` loads marketplace metadata from
`plugin-sources/marketplace.yaml`, renders Codex and Claude Code manifests from
that metadata, renders full plugin trees from `plugin-sources/`, and
materializes shared package code from `packages/` into each runtime artifact's
`_packages/` directory.

`shared-skills` is organized around workflow artifacts rather than general
advice. `requirements-packet` normalizes requests into traceable requirement
IDs, and related skills carry those IDs through specs, plans, implementation
evidence, verification gates, research ledgers, and scenario-based downstream
test plans. `shared-subagents` routes review work to focused gates such as
`test-adequacy-reviewer`, so tests written through the plugins must justify
fixtures and mocks against observable user scenarios.

For project-level Codex setup, use `docs/session-memory/AGENTS.block.md` as the
copy-paste session policy block for `AGENTS.md`. For shared workflow setup, use
`docs/shared-skills/AGENTS.block.md` and
`docs/shared-subagents/AGENTS.block.md` as copy-paste policy blocks for
`AGENTS.md` or `CLAUDE.md`. The split keeps `session-memory` checkpoint/resume
policy, `shared-skills` workflow artifact triggers, and `shared-subagents`
delegated review policy separate.

## Why `plugin-sources/`

This repository uses `plugin-sources/` instead of a top-level `src/` directory
because the canonical inputs are plugin manifests, skills, agents, docs, and
metadata rather than one application runtime. The explicit name keeps the source
boundary visible and avoids confusing canonical plugin material with generated
plugin packages or Python implementation code.

## Build And Validation

Run the plugin build and validation workflow from the repository root:

```bash
python tools/build_plugins.py
python tools/validate_generated.py
pytest
git diff --exit-code
test -z "$(git status --porcelain --untracked-files=all)"
```

The `validate-generated` GitHub Actions workflow follows the same contract:
regenerate plugin artifacts, validate generated outputs, run tests, detect
tracked drift with `git diff --exit-code`, detect untracked generated files with
`git status --porcelain --untracked-files=all`, and fail if the working tree
changes. CI installs `pytest` explicitly and does not auto-commit generated
changes; contributors must commit source updates and regenerated artifacts
together.
