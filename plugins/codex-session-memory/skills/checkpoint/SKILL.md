---
name: checkpoint
description: Prepare and verify a Codex session-memory checkpoint. Use when the user wants to save, checkpoint, persist current work, mark a milestone, or capture progress before risky changes.
---

# Session Memory Checkpoint

Create a checkpoint through an active-Codex handoff. The helper script gathers deterministic state and evidence; the current Codex writes the context file and updates the session index.

## Workflow

Run the `checkpoint.py` script next to this `SKILL.md` file:

```bash
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py prepare
```

Use the printed `context_path`, `index_path`, offsets, evidence, and required section template. The active Codex must then:

- write the context body to `context_path` using the prepare template and project AGENTS.md rules;
- update `INDEX.md` with the printed `index_entry` list item shape;
- record the printed frontmatter/update keys, including `last_processed_offset` set to the new offset;
- avoid writing secrets, `.env` contents, API keys, tokens, or personal identifiers.

After writing the files, verify the result:

```bash
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py verify /path/to/context.md
```

`verify` succeeds only when the context file is under `<root>/.codex/sessions/*/contexts/`, all required headings are present as exact Markdown heading lines, and `INDEX.md` contains a context list entry like `- [CONTEXT-...md]`.

## Notes

- The helper does not spawn another Codex process.
- The helper does not write the context body or update `INDEX.md`.
- Suggested context paths include seconds and are best-effort only; the active Codex must still handle collisions before writing.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration, then falls back to git toplevel / AGENTS.md / `.codex` / cwd.
