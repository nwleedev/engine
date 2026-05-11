---
name: status
description: Show session-memory status for the current Codex session — pending turns since last save, context files written, last save time, JSONL path, and AGENTS.md rule status. Use when the user wants to inspect or check the state of session memory before deciding whether to checkpoint.
---

# Session Memory Status

Read-only status report. It also reports whether the project AGENTS.md has the session-memory rules installed, partially present, missing, or not found.

## Run

```
python3 /path/to/session-memory/skills/status/status.py
```
