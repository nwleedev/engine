---
name: status
description: Show session-memory status for the current Codex session — pending turns since last save, context files written, last save time, JSONL path, and AGENTS.md rule status. Use when the user wants to inspect or check the state of session memory before deciding whether to checkpoint.
---

# Session Memory Status

Read-only status report. It also reports whether the project AGENTS.md has the codex-session-memory rules installed, partially present, missing, or not found.

Status reports the current flat artifact path under
`<root>/.codex/session-memory/threads/<CODEX_THREAD_ID>/` when it exists.
Legacy `.codex/sessions/*` and `.codex/sessions/_children/*` paths are only
fallback read locations; `_children` is deprecated and new checkpoints do not
create it.

Flat `INDEX.md` frontmatter does not make `role` or `parent_session_id`
authoritative. Status reads parent-child relationships from the Codex graph
when available. If graph lookup is degraded, it can print `Graph: unavailable`
and fall back to `parent_locator` / `graph_store` diagnostics or legacy
frontmatter only for compatibility reporting.

## Run

```
python3 /path/to/codex-session-memory/skills/status/status.py
```
