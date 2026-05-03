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
- update `INDEX.md` so it references the new context filename;
- record offset metadata such as `last_processed_offset` according to the session-memory rules;
- avoid writing secrets, `.env` contents, API keys, tokens, or personal identifiers.

After writing the files, verify the result:

```bash
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py verify /path/to/context.md
```

`verify` succeeds only when the context file exists, all required headings are present, and `INDEX.md` references the context filename.

## Notes

- The helper does not spawn another Codex process.
- The helper does not write the context body or update `INDEX.md`.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration, then falls back to git toplevel / AGENTS.md / `.codex` / cwd.
