---
description: Set up a professional non-development domain environment via brainstorming-style dialogue. Generates skill.md, rubric.md, and a task workflow command.
---

# /nondev-setup

Argument: $ARGUMENTS

**REQUIRED SUB-SKILL:** Use the `nondev-builder` skill to handle this command.

Invoke the nondev-builder skill now. Pass `$ARGUMENTS` as the invocation argument so
the skill can determine the correct mode:

- No argument → auto-detect mode (reads project files to infer domain)
- Hyphenated slug (e.g. `market-research`) → slug mode (use directly as task-name)
- Natural language sentence (e.g. "주식 시장 단기 투자 분석이 필요합니다") → natural-language mode
  (skill proposes 2-3 task-name candidates for user selection)

The skill will guide you through a 6-item brainstorming loop (1 question per turn),
run parallel web search for professional standards, and generate three artifact files:
`.claude/nondev/<task-name>/skill.md`, `.claude/nondev/<task-name>/rubric.md`,
and `.claude/commands/<task-name>.md`.
