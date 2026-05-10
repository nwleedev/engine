# Plugin Architecture

engine is a multi-harness plugin monorepo. The repository is moving toward one
canonical plugin source boundary that renders harness-specific plugin layouts
for Codex and Claude Code.

## Repository Layout

| Path | Role |
| --- | --- |
| `plugin-sources/` | Canonical source material for marketplace metadata and migrated shared plugin assets. |
| `packages/` | Runtime-agnostic Python logic shared by build and validation tools. |
| `renderers/` | Harness renderers that translate canonical inputs into plugin artifacts. |
| `plugins/codex/` | Generated Codex plugin artifacts, one directory per public plugin family. |
| `plugins/claude/` | Generated Claude Code plugin artifacts, one directory per public plugin family. |
| `docs/` | Public repository documentation that should be committed and reviewed. |
| `local-docs/` | Ignored planning and task notes for local work, not public documentation. |

Some source migrations are still in progress. For example,
`plugin-sources/marketplace.yaml` is the canonical marketplace source, and
`plugin-sources/shared-skills/` is the canonical shared-skills source, while
other plugin family source moves land in later tasks. Current build coverage is
therefore narrower than the final architecture: manifests and marketplace files
are generated for all public plugin families, while full tree materialization is
currently implemented for `shared-skills`.

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
families, renders marketplace metadata, and materializes migrated plugin trees
such as `shared-skills`. Later migration tasks extend this source-to-artifact
coverage to additional plugin families.

`python tools/validate_generated.py` checks that generated outputs are
structurally valid and in sync with the current source model.

For regular development, also run the relevant tests and check for generated
drift before committing.
