---
name: checkpoint
description: Prepare and verify a Codex session-memory checkpoint. Use when the user wants to save, checkpoint, persist current work, mark a milestone, or capture progress before risky changes.
---

# Session Memory Checkpoint

Create a checkpoint through an active-Codex handoff. The helper script gathers deterministic state and evidence; the current Codex writes the context file and updates the session index.

## Workflow

Run the `checkpoint.py` script next to this `SKILL.md` file.

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare
```

For subagent/review child sessions, parent selection uses explicit `--parent`
first, then `CODEX_SESSION_PARENT_ID`, then automatic detection.

In normal child-session use, run:

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare --role child
```

Within automatic detection, the helper reads rollout `session_meta` before state
DB. If rollout metadata identifies a child but lacks parent id, the helper still
checks state DB for a matching parent edge before failing closed. State DB
fallback checks `thread_spawn_edges` first, then `threads.source`.
State DB fallback is read-only and checks candidate homes in this order:
explicit `sqlite_home`, `CODEX_SQLITE_HOME`, Codex `config.toml` `sqlite_home`,
project `.codex`, then user `~/.codex`.

If automatic detection fails, retry with the parent session id explicitly:

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare --role child --parent <parent-session-id>
```

Use the printed `context_path`, `index_path`, offsets, evidence, and required section template. New checkpoints are written under `<root>/.codex/session-memory/threads/<thread-id>/`. The active Codex must then:

- write the context body to `context_path` using the prepare template and project AGENTS.md rules;
- preserve the full 9-section CONTEXT handoff: `current_goal`, `executive_summary`, `detailed_state`, `decisions`, `files`, `verification`, `risks`, `next_actions`, and `graph_context`;
- in `graph_context`, record graph availability diagnostics from the helper, including `unavailable`, `source`, `confidence`, `reason`, and `warnings` when they are present;
- append the printed `index_entry` list item to `INDEX.md`; do not rewrite or delete prior context entries, even when appending to the same HH00 context file;
- record only the printed frontmatter/update keys, including `session_id`, `last_processed_offset` set to the new offset, and `last_updated`;
- do not write `role` or `parent_session_id` as flat `INDEX.md` source fields; parent-child relationships come from the Codex graph or `parent_locator` / `graph_store` diagnostics, and any printed relationship diagnostics are not INDEX frontmatter;
- for child sessions, do not create new `_children` paths or parent `Child Sessions` entries; `_children` is legacy read and migration input only;
- avoid writing secrets, `.env` contents, API keys, tokens, or personal identifiers.

After writing the files, verify the result:

```bash
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py verify /path/to/context.md
```

`verify` succeeds when the context file is under `<root>/.codex/session-memory/threads/*/contexts/`, all required headings are present as exact Markdown heading lines, and `INDEX.md` contains a context list entry like `- [CONTEXT-...md]`. For read compatibility, legacy `<root>/.codex/sessions/*/contexts/` and `<root>/.codex/sessions/_children/*/contexts/` paths are still accepted.

## Notes

- The helper does not spawn another Codex process.
- The helper does not write the context body or update `INDEX.md`.
- Required context headings are `current_goal`, `executive_summary`, `detailed_state`, `decisions`, `files`, `verification`, `risks`, `next_actions`, and `graph_context`; this template preserves more useful handoff detail rather than reducing saved context.
- Suggested context paths use `CONTEXT-YYYYMMDD-HH00-checkpoint.md`; if that file already exists, append a new section to it and append a new `INDEX.md` entry.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration, then falls back to git toplevel / AGENTS.md / `.codex` / cwd.
