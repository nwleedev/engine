# Migration Guide

engine is moving from flat plugin paths to generated, harness-specific paths.
The current target shape is:

| Previous flat path | Generated Codex path | Generated Claude Code path |
| --- | --- | --- |
| `plugins/session-memory` | `plugins/codex/session-memory` | `plugins/claude/session-memory` |
| `plugins/quality-guard` | `plugins/codex/quality-guard` | `plugins/claude/quality-guard` |
| `plugins/shared-skills` | `plugins/codex/shared-skills` | `plugins/claude/shared-skills` |
| `plugins/shared-subagents` | `plugins/codex/shared-subagents` | `plugins/claude/shared-subagents` |
| `plugins/harness-foundry` | `plugins/codex/harness-foundry` | `plugins/claude/harness-foundry` |

Older flat directories may appear in history, but current generated artifacts
live only under harness-specific paths. Treat `plugin-sources/marketplace.yaml`
as the source of truth for current public harness paths.

## No Compatibility Directories

The migration target does not create compatibility directories for old physical
paths. Do not add new shim directories such as `plugins/session-memory` to
forward to generated harness-specific outputs.

Flat plugin directories are not current generated artifacts. Consumers should
update local references to the Codex or Claude Code path that matches their
harness.

## Preserve Public Identifiers

Preserve public plugin IDs, harness entrypoints, and marketplace identifiers
unless a breaking change is intentionally documented. Public plugin IDs are the
stable cross-harness identity, while harness-specific names can differ when the
host requires it.

For example, the public `session-memory` plugin can render as
`plugins/codex/session-memory` with the Codex marketplace name
`codex-session-memory`, and as `plugins/claude/session-memory` with the Claude
Code marketplace name `session-memory`.

When changing a public identifier, document the break, migration path, and the
affected marketplace entry in the same change.
