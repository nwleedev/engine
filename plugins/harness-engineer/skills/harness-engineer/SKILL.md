---
name: harness-engineer
description: Use when the user runs /create-harness, /update-harness, or /evaluate-harness. Also apply when editing code files to check harness compliance — look for patterns defined in .claude/harness/*.md files.
---

# Harness Engineer

Harness files define the **ideal** standard for a project domain.
They do NOT reflect the current codebase — they define what it should become.

## /create-harness

When the user runs `/create-harness` with a natural language description of their tech stack:

1. **Extract tech stack from the user's prompt**
   - Identify frameworks, libraries, and folder structure hints
   - Examples: "NextJS + TanStack Query + React Hook Form", "FastAPI + SQLAlchemy + PostgreSQL"

2. **Fetch official documentation** (Context7 / Tavily MCP)
   - Collect best practice patterns and anti-patterns from official docs
   - Prefer official docs and official example code over blog posts

3. **Generate `file_patterns`**
   - Extension patterns: determined by tech stack (e.g. `*.tsx` for React, `*.py` for Python)
   - Path patterns: reflect folder structure hints in the prompt
     - monorepo + "apps/web" → `["apps/web/**/*.tsx", "*.tsx"]`
   - When no hints: use conventional patterns for the framework
     - Next.js → `["*.tsx", "*.jsx", "app/**", "pages/**", "src/**"]`
   - After generating, show the list to the user and prompt them to adjust if the project structure differs

4. **Generate `keywords`**
   - Derive from tech stack terminology (framework names, key APIs, key patterns)

5. **Domain name**: free naming based on tech stack (e.g. `nextjs-tanstack`, `python-fastapi`)

6. **Determine language**:
   - Read `HARNESS_LANGUAGE` env var
   - `auto` (default): use current conversation language
   - `ko` / `en`: use as specified

7. **Write to `.claude/harness/<domain>.md`**
   - Include: `file_patterns`, `keywords`, `## Core Rules` (from official docs), `## Pattern Examples` with `<Good>`/`<Bad>` tags, `## Anti-Pattern Gate`
   - Confirm before overwriting existing files

8. **Show `file_patterns` to user**
   - "If this doesn't match your project structure, edit the `file_patterns:` list in `.claude/harness/<domain>.md`"

### Writing Rules

- `## Core Rules` section: checklist format, 5-8 items max
- `<Good>/<Bad>` examples: always include one-line reason after code block
- `## Anti-Pattern Gate`: self-check questions in code block format
- File length: stay under 500 lines

## /update-harness

When the user runs `/update-harness [domain]`:

1. Read `.claude/harness/violations.log` for the domain
2. Read the current harness file
3. For each repeated violation (appearing 3+ times):
   - Propose adding it to `## Anti-Pattern Gate`
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
Before writing code, run through the `## Anti-Pattern Gate` mentally.
If existing code violates harness rules, point it out and suggest a fix.
