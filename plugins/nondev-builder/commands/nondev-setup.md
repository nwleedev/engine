---
description: Set up a professional non-development domain environment via brainstorming-style dialogue. Generates skill.md, rubric.md, and a task workflow command.
---

# /nondev-setup

Argument: $ARGUMENTS

**REQUIRED SUB-SKILL:** Use the `nondev-builder` skill to handle this command.

Invoke the nondev-builder skill now. Pass `$ARGUMENTS` as the invocation argument so
the skill can determine the correct mode:

- No argument → **auto-detect mode** (reads project files to infer domain)
- Argument matches `[a-z0-9-]+` (lowercase letters, digits, hyphens only, no spaces) →
  **slug mode** (use directly as task-name; e.g. `market-research`, `stock-analysis-2026`)
- Anything else (spaces, uppercase, non-ASCII, mixed) → **natural-language mode**
  (skill proposes 2-3 task-name candidates; e.g. "주식 시장 단기 투자 분석이 필요합니다", "stock analysis")

The skill will guide you through a 6-item brainstorming loop (1 question per turn),
run parallel web search for professional standards, and generate three artifact files:
`.claude/nondev/<task-name>/skill.md`, `.claude/nondev/<task-name>/rubric.md`,
and `.claude/commands/<task-name>.md`.
