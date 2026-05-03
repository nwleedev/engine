---
name: install
description: Use when setting up codex-session-memory in a project or verifying that AGENTS.md contains the checkpoint, resume, and status workflow rules.
---

# Session Memory Install

Inspect the current project's AGENTS.md for codex-session-memory rules.

## Run

```bash
python3 /path/to/codex-session-memory/skills/install/install.py [en|ko]
```

## Behavior

- Reads AGENTS.md from the resolved project root.
- Reports `installed`, `partial`, `missing`, or `not found`.
- Prints a recommended markdown block for `missing`, `partial`, or `not found` status.
- Does not modify files.

## User-visible output

After running the script, always relay the script stdout to the user.

- If status is `installed`, summarize that AGENTS.md already contains the rules.
- If status is `partial`, `missing`, or `not found`, include the full recommended block from stdout in the assistant response.
- Treat exit code 1 from `partial`, `missing`, or `not found` as an expected diagnostic result, not as a reason to omit stdout.
- Do not paraphrase or drop the `Add this block:` section.
- Do not edit AGENTS.md unless the user explicitly asks.
