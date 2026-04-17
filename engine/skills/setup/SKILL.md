---
name: setup
description: "Initialize project files for the engine plugin. Copies templates/CLAUDE.md.example -> CLAUDE.md and templates/engine.env.example -> engine.env when missing."
user-invocable: true
---

# Engine Setup

Initialize missing project configuration files by copying from plugin templates.

---

## Files

| Target | Template (templates/) | Purpose |
|--------|----------------------|---------|
| `.claude/CLAUDE.md` | `templates/CLAUDE.md.example` (default) or `templates/CLAUDE.md.ko.example` (Korean) | Project rules for Claude Code |
| `.claude/engine.env` | `templates/engine.env.example` | Engine plugin settings (review/research perspectives) |
| `.gitignore` (patterns) | — | Harness-generated paths (sessions, memory, meta, feeds, temps) |
| `.claude/context-essentials.md` | — (created fresh) | Compact-safe context summary (≤50 lines) |

## Procedure

0. Resolve language: if the skill was invoked with an argument `ko` (e.g. `/engine:setup ko`), set `CLAUDE_TEMPLATE=templates/CLAUDE.md.ko.example`. Otherwise (no arg, `en`, or anything else), use `CLAUDE_TEMPLATE=templates/CLAUDE.md.example`
1. Check if `.claude/CLAUDE.md` exists (use Glob for `**/.claude/CLAUDE.md` or Read)
2. Check if `.claude/engine.env` exists
3. For each **missing** file:
   - Read the corresponding `.example` template from the `templates/` subdirectory (`${CLAUDE_TEMPLATE}` for `CLAUDE.md`, `templates/engine.env.example` for `engine.env`)
   - Write it to the target path
   - Report what was created (include the resolved template name)
4. For each **existing** file: skip and report that it already exists
5. If both files already exist: report that setup is complete, no action needed
6. Ensure `.gitignore` includes harness-generated paths:
   - Target: `<project-root>/.gitignore`
   - Patterns (exact-match, append-only): `.claude/sessions/`, `.claude/agent-memory/`, `.claude/meta/`, `.claude/feeds/`, `temps/`
   - If `.gitignore` does not exist: create it with exactly these 5 lines (one per line, with a trailing newline after the last line)
   - If `.gitignore` exists: Read the file, then for each pattern check exact-line match (`grep -Fxq "$pattern" .gitignore`). Skip if present, append if absent. When appending, ensure the file ends with a newline before the new line (read the last byte; if it is not `\n`, add one first) to prevent the pattern from being glued to the final existing line
   - Report: list of patterns that were appended; if the file was newly created, mark "created"
   - Never remove, reorder, or modify existing `.gitignore` entries
7. Initialize `.claude/context-essentials.md` if it does not exist:
   - Check if `.claude/context-essentials.md` exists
   - If missing: create it with the following template (adapt `<branch>`, `<goal>`, `<file1>`–`<file3>` to the project):
     ```markdown
     # Context Essentials
     <!-- Max 50 lines. Injected on compact events. Keep this file concise. -->

     ## Branch / Goal
     - Branch: <branch>
     - Goal: <goal>

     ## Forbidden Patterns
     - (add up to 5 project-specific forbidden patterns here)

     ## Key Files
     - <file1>
     - <file2>
     - <file3>

     ## Active Plan
     <!-- For LLM reference only — session-restore.sh reads plan path from
          $SESSION_DIR/.current-plan or .claude/plans/*.md, not from this file -->
     - (path to active plan file, if any)
     ```
   - Report what was created
   - If it already exists: skip and report

## Important

- **Never overwrite** existing files — only copy when the target is missing
- After creating `CLAUDE.md`, suggest the user review the `## Project-Specific Rules` section to add their own rules
- After creating `engine.env`, suggest the user uncomment and customize the settings they need
- `context-essentials.md` must stay ≤50 lines — it is injected verbatim on compact events and must not overflow context
- After creating `context-essentials.md`, suggest the user fill in their branch/goal, forbidden patterns, and key file paths
- `.gitignore` edits are append-only — never remove or reorder existing lines
- When `.gitignore` is missing, create it; when present, only append new patterns
- Template locations (`templates/` subdirectory):
  - `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md.example` (default, English)
  - `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md.ko.example` (Korean variant, selected when invoked as `/engine:setup ko`)
  - `${CLAUDE_PLUGIN_ROOT}/templates/engine.env.example`
- Language selection applies only to `CLAUDE.md` creation. It has no effect when `.claude/CLAUDE.md` already exists or when only `engine.env` / `.gitignore` work is performed
