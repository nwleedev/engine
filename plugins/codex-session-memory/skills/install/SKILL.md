---
name: install
description: Check whether the current project AGENTS.md contains codex-session-memory workflow rules. Use when setting up this plugin in a project or verifying that checkpoint/resume/status rules are installed. This skill prints a patch proposal only and does not edit AGENTS.md.
---

# Session Memory Install

Inspect the current project's AGENTS.md for codex-session-memory rules.

## Run

```bash
python3 /path/to/codex-session-memory/skills/install/install.py
```

## Behavior

- Reads AGENTS.md from the resolved project root.
- Reports `installed`, `partial`, `missing`, or `not found`.
- Prints a recommended markdown block when rules are missing.
- Does not modify files.
