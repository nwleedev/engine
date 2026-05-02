---
name: checkpoint
description: Save the current Codex session as an incremental context summary by forcing a narration checkpoint. Use when the user wants to save, checkpoint, or persist their current work, mark a milestone, or capture progress before risky changes.
---

# Session Memory Checkpoint

Force a narration checkpoint for the current Codex session. Reads transcript delta since last save, generates structured summary via codex-exec, writes to `<root>/.codex/sessions/<thread_id>/INDEX.md` and `contexts/CONTEXT-*.md`.

## Run

Run the `checkpoint.py` script next to this `SKILL.md` file via your shell tool:

```
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py
```

Output is a single status line. Full narration goes to file — parent session context unaffected.

## Notes

- Latency ~15-60s (codex-exec baseline overhead).
- Idempotent: forces a checkpoint marker even if no new turns since last save.
- Project root resolution honors `CODEX_PROJECT_DIR` env or `.env` declaration; falls back to git toplevel / AGENTS.md / .codex / cwd.
