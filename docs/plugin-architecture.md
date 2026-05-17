# Plugin Architecture

engine is a multi-harness plugin monorepo. The repository uses one canonical
plugin source boundary that renders harness-specific plugin layouts for Codex
and Claude Code.

## Repository Layout

| Path | Role |
| --- | --- |
| `plugin-sources/` | Canonical source material for marketplace metadata, adapter trees, shared skills, shared subagents, and harness-foundry material. |
| `packages/` | Runtime-agnostic Python logic shared by build and validation tools. |
| `renderers/` | Harness renderers that translate canonical inputs into plugin artifacts. |
| `plugins/codex/` | Generated Codex plugin artifacts, one directory per public plugin family. |
| `plugins/claude/` | Generated Claude Code plugin artifacts, one directory per public plugin family. |
| `docs/` | Public repository documentation that should be committed and reviewed. |
| `local-docs/` | Ignored planning and task notes for local work, not public documentation. |

`plugin-sources/marketplace.yaml` is the canonical marketplace source. The full tree materialization is implemented for `session-memory`, `quality-guard`, `shared-skills`, `shared-subagents`, and `harness-foundry`.
`deep-research-prompt-export` is also rendered as a generated Codex and Claude
Code plugin, with the stable internal Python import package copied into
`_packages/`.
Runtime-agnostic
package code from `packages/` is copied into generated artifacts under
`_packages/`. For example, `plugin-sources/shared-skills/` renders to both
`plugins/codex/shared-skills/` and `plugins/claude/shared-skills/`.

The workflow plugins enforce traceability across Codex and Claude Code instead
of publishing loose advice. `shared-skills` starts with `requirements-packet`
and carries requirement IDs through spec contracts, plan contracts,
implementation evidence, verification gates, research source ledgers, and
scenario test contracts. `shared-subagents` keeps routing explicit by sending
requirement fidelity, plan fidelity, citation checks, test adequacy,
completion closure, and residual risk to separate roles such as
`test-adequacy-reviewer`.

Use `docs/shared-workflow/AGENTS.block.md` as the repository-owned copy-paste
policy block for project `AGENTS.md` or `CLAUDE.md` setup. It routes both
`shared-skills` workflow artifacts and `shared-subagents` delegated review
roles, so it is public repository documentation rather than a file owned by one
plugin bundle.

## Source And Generated Boundary

Do not edit generated plugin artifacts directly when the same content is
derived from canonical source. Change the source under `plugin-sources/`, shared
logic under `packages/`, or renderer behavior under `renderers/`, then rebuild
the generated artifacts.

Use this marker in generated files or reviews when needed:

```text
Do not edit generated artifacts directly.
```

Generated artifacts under `plugins/codex/` and `plugins/claude/` are committed
so users can install or inspect plugins without running the build pipeline.
Commit source changes and regenerated artifacts together so the repository does
not drift.

## Build And Validation

Run these commands from the repository root after changing canonical plugin
source, renderers, or generated plugin artifacts:

```bash
python tools/build_plugins.py
python tools/validate_generated.py
```

`python tools/build_plugins.py` reads marketplace metadata from
`plugin-sources/marketplace.yaml`, renders harness manifests for public plugin
families, renders marketplace metadata, materializes plugin trees from
`plugin-sources/`, and copies runtime-agnostic package code from `packages/`
into generated `_packages/` directories.

`python tools/validate_generated.py` checks that generated outputs are
structurally valid and in sync with the current source model.

For regular development, also run the relevant tests and check for generated
drift before committing.
