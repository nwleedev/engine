---
name: harness-engineer
description: Use when the user runs /create-harness, /update-harness, or /evaluate-harness. Also apply when editing code files to check harness compliance — look for patterns defined in .claude/harness/*.md files.
---

# Harness Engineer

Harness files define the **ideal** standard for a project domain.
They do NOT reflect the current codebase — they define what it should become.

## /create-harness

When the user runs `/create-harness [domains]`:

1. If no domains specified, scan the project:
   - `*.tsx` or `*.jsx` present → propose `react-frontend`
   - `*.py` present → propose `python-backend`
   - `docs/research/` or similar → propose `market-research`
   - Present candidate list and wait for confirmation

2. Determine language:
   - Read `HARNESS_LANGUAGE` env var
   - `auto` (default): use current conversation language
   - `ko` / `en`: use as specified

3. For each domain, load the template from `skills/harness-engineer/templates/<domain>.md`
   - Customize `<Good>/<Bad>` examples to match the project's actual code style
   - Do NOT copy bad patterns from existing code
   - Base rules on official documentation standards

4. Write to `.claude/harness/<domain>.md`
   - Confirm before overwriting existing files

5. Summarize what was created

### Writing Rules

- `## 핵심 규칙` section: checklist format, 5-8 items max
- `<Good>/<Bad>` examples: always include one-line reason after code block
- `## 안티패턴 게이트`: self-check questions in code block format
- File length: stay under 500 lines

## /update-harness

When the user runs `/update-harness [domain]`:

1. Read `.claude/harness/violations.log` for the domain
2. Read the current harness file
3. For each repeated violation (appearing 3+ times):
   - Propose adding it to `## 안티패턴 게이트`
   - Propose a `<Bad>` example showing the violation pattern
4. For abstract rules without code examples: propose adding `<Good>/<Bad>` pairs
5. Confirm each change before writing
6. Update `updated:` date in frontmatter

## /evaluate-harness

When the user runs `/evaluate-harness [domain]`:

Score each criterion out of 10:

| Criterion | How to score |
|-----------|-------------|
| Pattern example concreteness | 10 = all rules have `<Good>/<Bad>` code examples |
| Anti-pattern coverage | 10 = violations.log entries all appear in gate |
| File length | 10 = under 500 lines; deduct 2 per 100 lines over |
| Violations reflected | 10 = no repeated violations missing from gate |
| Recency | 10 = updated within 30 days; deduct 1 per week older |

Output the table with scores, comments, and overall recommendation.
If score < 7: recommend `/update-harness <domain>`.

## Compliance During Work

When editing code files, check `.claude/harness/` for the relevant domain.
Before writing code, run through the `## 안티패턴 게이트` mentally.
If existing code violates harness rules, point it out and suggest a fix.
