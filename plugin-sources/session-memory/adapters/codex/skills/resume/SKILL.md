---
name: resume
description: Resume a prior Codex session by loading its INDEX.md context summary into the current session. Use after context compaction in the same session as the first action, or when the user explicitly asks to load a prior session by prefix.
---

# Session Memory Resume

List or load saved sessions for the current project.

Saved sessions are graph-first flat artifacts under
`<root>/.codex/session-memory/threads/<CODEX_THREAD_ID>/INDEX.md` with context
files in `contexts/`. Legacy `.codex/sessions/*` and
`.codex/sessions/_children/*` artifacts can still be read for compatibility,
but `_children` is deprecated and new checkpoints do not create it.

Flat `INDEX.md` frontmatter does not use `role` or `parent_session_id` as the
relationship source of truth. Parent-child relationships come from the Codex
graph, or from `parent_locator` / `graph_store` diagnostics when graph data is
unavailable. If graph lookup is unavailable, resume still loads the selected
flat artifact and recent context files so the work can continue from the
durable handoff.

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

The compact handoff includes the flat `INDEX.md`, recent 9-section CONTEXT
files, and any related graph context that can be resolved without treating
relationship frontmatter as authoritative.
