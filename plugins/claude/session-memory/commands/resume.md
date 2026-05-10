---
description: List sessions of this project and inject a chosen session's INDEX
argument-hint: ""
---

# Resume Session Context

You will help the user pick another session of this same project to inject as context.

## Steps

1. Determine project root via `git rev-parse --show-toplevel` (Bash). If it fails, use the current working directory.
2. List directories under `<project_root>/.claude/sessions/` excluding names starting with `_` (archive) or `.` (hidden) using Bash `ls -1`.
3. For each directory, Read its `INDEX.md` (limit 50 lines) and parse the YAML frontmatter to extract `session_id`, `last_updated`, and the first context entry's one-liner.
4. Display a markdown table with columns: `#`, `session_id (8 chars)`, `last_updated`, `summary`. Sort by `last_updated` descending. Limit to 10 rows.
5. Ask the user: "Which session to inject? (number or 8-char session_id prefix)"
6. After the user replies, identify the matching session.
7. Read the full `INDEX.md` of the chosen session, truncate to ≤8000 chars, and emit a final assistant message with the content wrapped in `<session-resume>` tags. Add a brief note: "Use Read on `.claude/sessions/<id>/contexts/*.md` for details."

## Constraints

- Do not modify any files.
- Do not auto-load context files — only the INDEX.
- If no sessions are found, say so clearly and stop.
