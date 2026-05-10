# engine

engine is a multi-harness plugin monorepo for Codex and Claude Code.

The repository separates plugin source material, shared domain logic,
harness-specific renderers, and generated plugin artifacts. That structure is
being introduced in stages so current generated outputs stay reproducible while
more plugin families move behind the same source boundary.

## Repository Layout

| Path | Purpose |
|---|---|
| `plugin-sources/` | Current canonical source for marketplace metadata and shared-skills reference material. |
| `packages/` | Runtime-agnostic Python domain logic shared by build and validation tools. |
| `renderers/` | Harness renderers that translate canonical source into Codex and Claude Code plugin layouts. |
| `plugins/codex/<plugin>` | Generated Codex plugin artifacts. |
| `plugins/claude/<plugin>` | Generated Claude Code plugin artifacts. |

Do not edit generated plugin artifacts directly when an equivalent source file
already exists under `plugin-sources/`. Change that source, update shared logic
in `packages/`, or update harness output rules in `renderers/`, then regenerate
the artifacts. Some generated manifests exist before their full plugin source
trees have migrated; those families will move into `plugin-sources/` in later
tasks.

## Plugin Families

The core plugin families include `session-memory` and `quality-guard`.

The current generated multi-harness families include `shared-skills`,
`shared-subagents`, and `harness-foundry`. Today, `tools/build_plugins.py`
loads marketplace metadata from `plugin-sources/marketplace.yaml`, renders
Codex and Claude Code manifests from that metadata, and renders the
`shared-skills` trees from `plugin-sources/shared-skills/`. Full canonical
source migration for `shared-subagents`, `harness-foundry`, and other plugin
family material follows in later tasks.

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
