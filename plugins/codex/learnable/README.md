<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/README.md -->

# Learnable

Learnable stores project explanations as local Markdown materials under `.codex/materials` and serves them through a read-only local viewer.

Use `learnable:entry` as the only Codex entry skill. The MVP does not provide a browser prompt input UI, remote sync, background job queue, or automatic session-memory checkpointing for material-only work.

See [policy](references/policy.md) for project policy guidance and [session model](references/session-model.md) for the material graph model.

## Optional AGENTS.md Block

Copy this block into a project `AGENTS.md` only when the project wants durable Learnable reminders. If this block is missing, Learnable still works in MVP through its installed skills and references. Re-review this block before adding browser prompt UI or automated workers.

```markdown
<!-- LEARNABLE-WORKFLOW-START -->
## Learnable Workflow

- Use `$learnable:entry` (`learnable:entry`) when a user asks Learnable to explain project code, files, workflows, or saved materials.
- Learnable material graph identity is `learnable_session_id`, `node_id`, and `parent_node_id`; Codex/Claude session IDs are provenance only.
- During `.codex/materials/`-only material generation, do not run `$session-memory:checkpoint` unless the user explicitly asks.
- Learnable must not create, mutate, migrate, or clean `.codex/session-memory/`.
- Detailed policy lives in the installed Learnable plugin README/references; do not require project-local `docs/learnable/*`.
- Do not follow Learnable workflow instructions when the Learnable plugin is not installed.
<!-- LEARNABLE-WORKFLOW-END -->
```
