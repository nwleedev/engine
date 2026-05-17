---
name: checkpoint
description: Prepare and verify a Codex session-memory checkpoint. Use when the user wants to save, checkpoint, persist current work, mark a milestone, or capture progress before risky changes.
---

# Session Memory Checkpoint

Create a checkpoint for the explicit `CODEX_SESSION_ID` session-memory artifact target.
`CODEX_THREAD_ID` is used only to locate the active rollout JSONL; it is not used
as the artifact destination.

## Workflow

Run the `checkpoint.py` script next to this `SKILL.md` file.

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare
```

`prepare` requires both `CODEX_SESSION_ID` and `CODEX_THREAD_ID`. If they differ,
it prints a warning and still writes only under
`<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/`.

The helper writes the context file and updates `INDEX.md` directly. It extracts
the latest transcript delta and durable evidence into the full 9-section CONTEXT
handoff: `current_goal`, `executive_summary`, `detailed_state`, `decisions`,
`files`, `verification`, `risks`, `next_actions`, and `graph_context`.

The context metadata records `session_id`, `source_thread_id`, `task_id`,
`checkpoint_id`, and `created_at`. `graph_context` records that Codex graph and
parent discovery are not used. The checkpoint path uses:

```text
contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md
```

`INDEX.md` is updated with an `INDEX.md.lock`, writer-scoped backup/temp files,
same-directory temp writes, file fsync, and `os.replace()`. If context writing
succeeds but `INDEX.md` update fails, the context file is preserved and the
helper exits with code `1` plus repair guidance.

After writing the files, verify the result:

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
- Required context headings are `current_goal`, `executive_summary`, `detailed_state`, `decisions`, `files`, `verification`, `risks`, `next_actions`, and `graph_context`; the helper fills them from the latest transcript delta and extracted evidence.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration, then falls back to git toplevel / AGENTS.md / `.codex` / cwd.
