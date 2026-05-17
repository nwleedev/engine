---
name: status
description: Show artifact-only session-memory status for CODEX_SESSION_ID: artifact path, context count, last save metadata, pending offset, and AGENTS.md rule status.
---

# Session Memory Status

Read-only status report. It also reports whether the project AGENTS.md has the session-memory rules installed, partially present, missing, or not found.

Status reports only the current flat artifact path under
`<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/`. If
`CODEX_SESSION_ID` is missing, status prints a diagnostic and does not inspect
Codex graph state, sqlite state DBs, JSONL files, parent locators, child
session folders, or legacy `.codex/sessions/*` fallbacks.

If the `CODEX_SESSION_ID` artifact has not been checkpointed, status reports
the missing artifact path and stops after artifact-only diagnostics.

## Run

```
python3 /path/to/session-memory/skills/status/status.py
```
