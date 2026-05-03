---
name: resume
description: Resume a prior Codex session by loading its INDEX.md context summary into the current session. Use after context compaction in the same session as the first action, or when the user explicitly asks to load a prior session by prefix.
---

# Session Memory Resume

List or load saved sessions for the current project.

## Same-session compaction recovery

After manual or automatic context compaction in the same Codex session, run this skill first with the current session prefix so the active Codex reloads the handoff context.

## Cross-session resume

Do not auto-resume old sessions. When starting a new session, call this skill only when the user explicitly asks to continue a prior session.

## Run

No argument — list sessions:

```bash
python3 /path/to/codex-session-memory/skills/resume/resume.py
```

With 8-character session id prefix — print a compact handoff:

```bash
python3 /path/to/codex-session-memory/skills/resume/resume.py <prefix>
```
