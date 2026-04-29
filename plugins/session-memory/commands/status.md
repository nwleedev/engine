---
description: Show current session memory status (narrations, contexts, archive, recent log)
argument-hint: ""
---

# Session Memory Status

Run a Bash one-liner that:
1. Resolves project root via `git rev-parse --show-toplevel || pwd`.
2. Locates the current session by reading `$CLAUDE_SESSION_ID` env var if set; else lists `.claude/sessions/` directories sorted by mtime and picks the most recent.
3. For that session, prints:
   - Session ID (full + 8-char short)
   - `started`, `last_updated` (from INDEX frontmatter)
   - Number of CONTEXT files in `contexts/`
   - Total size of `contexts/` (`du -sh`)
   - Last 5 narration decisions from `log.jsonl` (filter event in {Stop, PreToolUse, SessionEnd, ManualCheckpoint}), formatted as a table
   - Archive count: `ls .claude/sessions/_archive/*/*.tar.gz 2>/dev/null | wc -l`
4. Also report `INSIGHT.md` size and entry count.

Show the output as a fenced ```text``` block. Do not modify files.
