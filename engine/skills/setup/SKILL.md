---
name: setup
description: "Initialize project files for the engine plugin. Copies CLAUDE.md.example -> CLAUDE.md and engine.env.example -> engine.env when missing."
user-invocable: true
---

# Engine Setup

Initialize missing project configuration files by copying from plugin templates.

---

## Files

| Target | Template (plugin root) | Purpose |
|--------|----------------------|---------|
| `.claude/CLAUDE.md` | `CLAUDE.md.example` | Project rules for Claude Code |
| `.claude/engine.env` | `engine.env.example` | Engine plugin settings (review/research perspectives) |

## Procedure

1. Check if `.claude/CLAUDE.md` exists (use Glob for `**/.claude/CLAUDE.md` or Read)
2. Check if `.claude/engine.env` exists
3. For each **missing** file:
   - Read the corresponding `.example` template from the plugin root (`engine.env.example`, or `.claude/CLAUDE.md.example` in the project)
   - Write it to the target path
   - Report what was created
4. For each **existing** file: skip and report that it already exists
5. If both files already exist: report that setup is complete, no action needed

## Important

- **Never overwrite** existing files — only copy when the target is missing
- After creating `CLAUDE.md`, suggest the user review the `## Project-Specific Rules` section to add their own rules
- After creating `engine.env`, suggest the user uncomment and customize the settings they need
- Template locations depend on context:
  - Plugin root: `${CLAUDE_PLUGIN_ROOT}/engine.env.example` and `${CLAUDE_PLUGIN_ROOT}/../.claude/CLAUDE.md.example`
  - Project fallback: `.claude/engine.env.example` and `.claude/CLAUDE.md.example`
