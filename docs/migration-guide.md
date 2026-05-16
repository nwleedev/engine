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

## Breaking Workflow Route Redesign

The shared workflow plugins intentionally remove legacy active routes. Use the
new routes below when updating prompts, AGENTS guidance, or local project
instructions.

Shorthand mappings: requirements-clarifier -> requirements-packet,
spec-reviewer -> requirements-reviewer + plan-reviewer,
research-prompt -> deep-research-prompt-export.

| Legacy name | New route | Notes |
| --- | --- | --- |
| requirements-clarifier | requirements-packet | Requirements are now ID-based artifacts. |
| research-crosscheck | research-plan + source-ledger + claim-evidence-map | Research is split into planning, source inventory, and claim mapping. |
| task-planner | plan-contract | Plan tasks must link to requirement IDs and validation methods. |
| review-checklist | specialist reviewers | Review routing is split by requirement, plan, citation, test, closure, and risk. |
| verification-evidence | implementation-evidence + verification-gate | Evidence collection and completion gate are separate. |
| spec-reviewer | requirements-reviewer + plan-reviewer | Requirement fidelity and plan fidelity are distinct. |
| online-researcher | source-researcher | Source collection no longer owns decision synthesis. |
| research-prompt | deep-research-prompt-export | The plugin exports prompts for external ChatGPT Deep Research handoff. |
