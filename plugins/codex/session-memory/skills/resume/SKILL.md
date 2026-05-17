---
name: resume
description: Resume a prior Codex session by loading its INDEX.md context summary into the current session. Use after context compaction in the same session as the first action, or when the user explicitly asks to load a prior session by prefix.
---

# Session Memory Resume

List or load saved sessions for the current project.

Saved sessions are flat artifacts under
`<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/INDEX.md` with context
files in `contexts/`. Default resume is fail-closed: it requires
`CODEX_SESSION_ID` and reads only that artifact's `INDEX.md` plus recent context
files. Legacy `.codex/sessions/*` and `.codex/sessions/_children/*` artifacts
can still be read only through an explicit 8-character prefix, with normal
missing and ambiguity checks.

Resume does not use Codex graph state, sqlite state DBs, `parent_locator`, or
child discovery to augment or auto-select a session.

## Same-session compaction recovery

After manual or automatic context compaction in the same Codex session, run this skill first with the current session prefix so the active Codex reloads the handoff context.

## Cross-session resume

Do not auto-resume old sessions. When starting a new session, call this skill only when the user explicitly asks to continue a prior session.

## Run

No argument — print the current `CODEX_SESSION_ID` artifact handoff:

```bash
CODEX_SESSION_ID=<id> python3 /path/to/session-memory/skills/resume/resume.py
```

With 8-character session id prefix — print a compact handoff:

```bash
python3 /path/to/session-memory/skills/resume/resume.py <prefix>
```

The compact handoff includes the selected `INDEX.md` and recent 9-section
CONTEXT files only.
