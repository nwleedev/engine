---
name: checkpoint
description: Prepare and verify a Codex session-memory checkpoint. Use when the user wants to save, checkpoint, persist current work, mark a milestone, or capture progress before risky changes.
---

# Session Memory Checkpoint

Create a checkpoint for the explicit `CODEX_SESSION_ID` session-memory artifact target.
`CODEX_THREAD_ID` is used only to locate the active rollout JSONL; it is not used
as the artifact destination.

## Workflow

Run the `checkpoint.py` script next to this `SKILL.md` file. Treat `prepare`
as a handoff generator, not as the completed checkpoint.

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare
```

`prepare` requires both `CODEX_SESSION_ID` and `CODEX_THREAD_ID`. If they differ,
it prints a warning and still targets only
`<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/`.

`prepare` is intentionally output-only. It prints the artifact target, offset
metadata, extracted evidence, and the full 9-section CONTEXT template:
`current_goal`, `executive_summary`, `detailed_state`, `decisions`, `files`,
`verification`, `risks`, `next_actions`, and `graph_context`.

The template is a required structure, not a completed artifact. Filling it with
meaningful content is the active Codex's responsibility. Do not refuse or stop
because the template contains placeholders; replace placeholders using your
understanding of the current conversation and the printed evidence.

## Mandatory Active Codex Actions

After `prepare` succeeds, do not stop or report completion. The active Codex
must finish the checkpoint by doing all of the following:

1. Write the context file at the printed `context_path`.
2. Replace every `guidance:` line, `<title>`, and `<summary>` placeholder with
   meaningful handoff content derived from the printed evidence and current
   conversation.
3. Include all required headings exactly once, preserve the printed frontmatter
   metadata, and record `graph_status: not_used` / `graph_source: none`.
4. Update the printed `INDEX.md` target with a human-written summary entry for
   the context file and the printed `last_processed_offset`, `last_updated`,
   `session_id`, and `source_thread_id` metadata.
5. Run `checkpoint.py verify <context_path>` and treat a non-zero exit as an
   incomplete checkpoint that must be repaired before ending the turn.

The checkpoint is not complete if the context file is missing, `INDEX.md` is
missing the context entry, `verify` has not run, or the context still contains
`guidance:`, `<title>`, or `<summary>`.

The context metadata records `session_id`, `source_thread_id`, `task_id`,
`checkpoint_id`, and `created_at`. `graph_context` records that Codex graph and
parent discovery are not used. The checkpoint path uses:

```text
contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md
```

After the active Codex writes the files, verify the result:

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py verify /path/to/context.md
```

`verify` also requires `CODEX_SESSION_ID`. It succeeds when the context file is
under `<root>/.codex/session-memory/threads/*/contexts/`, all required headings
are present as exact Markdown heading lines, and `INDEX.md` contains a context
list entry like `- [CONTEXT-...md]`. For read compatibility, legacy
`<root>/.codex/sessions/*/contexts/` and
`<root>/.codex/sessions/_children/*/contexts/` paths are still accepted.

## Notes

- The helper does not spawn another Codex process.
- The helper does not read Codex sqlite DBs, `thread_spawn_edges`, `threads.source`, rollout `session_meta`, `parent_locator`, or `graph_store`.
- Required context headings are `current_goal`, `executive_summary`, `detailed_state`, `decisions`, `files`, `verification`, `risks`, `next_actions`, and `graph_context`; the helper prints a template and evidence, and the active Codex fills the final handoff document.
- Do not use the Codex sqlite DB, parent graph, or rollout `session_meta` to decide where to write; write only to the printed `CODEX_SESSION_ID` artifact target.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration, then falls back to git toplevel / AGENTS.md / `.codex` / cwd.
