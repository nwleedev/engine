---
name: harness-builder
description: Use when the user runs /harness-setup, /harness-sync, or /harness-audit. Orchestrates tech stack detection, web search, harness generation, linter config generation, and code auditing.
---

# Harness Builder

This skill runs in three modes determined by which command invoked it.

- `/harness-setup` → **setup mode**
- `/harness-sync` → **sync mode**
- `/harness-audit` → **audit mode**

---

## Setup Mode — `/harness-setup`

### Step 1: Detect Tech Stack

Run in a Bash tool call:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from stack_detector import detect_stack
import json
print(json.dumps(detect_stack('.')))
"
```

Parse the JSON output. Then:
- If `confidence == "low"`: ask — "I couldn't detect your stack automatically. What languages and frameworks does this project use?"
- If `monorepo == true`: ask — "Multiple sub-projects detected. Which one should I configure? (found package files in: [list subdirs])"

### Step 2: Web Search for Best Practices

Query both tools **in parallel** when both are available:

**Context7** — official docs and config schemas:
- Use `resolve-library-id` for each detected framework, then `query-docs` with: "[Framework] recommended project structure TypeScript configuration"
- Use `query-docs` for each missing linter: "[Linter] official configuration recommended rules"

**Tavily** — community patterns:
- `tavily_search`: "[Framework] [current year] best practices production ESLint rules"
- `tavily_search`: "[Framework] recommended architecture patterns file structure"

**Fallback order** when tools are unavailable:
1. Use whichever single tool is available
2. Claude Code built-in WebSearch / WebFetch
3. Training knowledge — prepend: "⚠️ Based on training data — verify against current official docs before using."

### Step 3: Generate Harness File

Create `.claude/harness/<domain>.md` with this structure:

```
---
domain: <hyphenated-slug>
domain_type: code
languages: [<from detection>]
frameworks: [<from detection>]
linters: [<linters to configure>]
file_patterns: [<glob patterns for this stack>]
keywords: [<key terminology from framework>]
updated: <YYYY-MM-DD today>
---

# <Display Name> Harness

## Purpose
<1-2 sentences defining what quality standard this harness enforces>

## Core Rules
- [ ] <Specific actionable rule from official docs>
(minimum 5 rules, sourced from web search results)

## Pattern Examples

<Good>
<concrete correct code example>
</Good>

<Bad>
<concrete anti-pattern code example>
</Bad>

## Anti-Pattern Gate
<3-5 questions to ask before editing files in this domain>
```

Name the domain as a hyphenated slug (e.g., `nextjs-typescript`, `python-fastapi`, `go-rest-api`).

If `.claude/harness/<domain>.md` already exists: ask the user before overwriting.

Run to write the file:
```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from harness_io import write_harness_file, harness_file_exists
# Check first, then write
print(harness_file_exists('.claude/harness', '<domain>'))
"
```

### Step 4: Generate Linter Config Files

For each linter in `linters_missing`:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from linter_config import get_linter_config_path, should_skip_existing
import json
linter = '<linter>'
eslint_version = '<eslint_version or None>'
skip = should_skip_existing(linter, '.')
if not skip:
    path, fmt = get_linter_config_path(linter, eslint_version if linter == 'eslint' else None, '.')
    print(json.dumps({'skip': False, 'path': path, 'format': fmt}))
else:
    print(json.dumps({'skip': True}))
"
```

For each linter that is not skipped:
- Generate config content based on web search (official recommended rules)
- Write to the returned path
- For `toml-section` format (ruff, clippy): append the `[tool.ruff]` or `[lints]` section to the existing TOML file

If skipped: inform user — "Skipped [linter]: config already exists."

### Step 5: Update Project CLAUDE.md

Check if `CLAUDE.md` in the current directory contains `## Harness Standards`.

If not, append this section to `CLAUDE.md`:

```markdown

## Harness Standards

Follow the quality standards defined in `.claude/harness/*.md`.
Before editing files matching a domain's `file_patterns`, consult the relevant harness.
Run `/harness-sync` to refresh standards after adding new dependencies.
```

If the section already exists: inform user — "Skipped CLAUDE.md update: Harness Standards section already present."

### Step 6: Output Install Guidance

List copyable install commands for each linter in `linters_missing`, using the detected package manager:

| Linter | npm | pnpm | yarn | other |
|---|---|---|---|---|
| eslint | `npm install --save-dev eslint` | `pnpm add -D eslint` | `yarn add -D eslint` | — |
| prettier | `npm install --save-dev prettier` | `pnpm add -D prettier` | `yarn add -D prettier` | — |
| stylelint | `npm install --save-dev stylelint` | `pnpm add -D stylelint` | `yarn add -D stylelint` | — |
| ruff | `pip install ruff` | — | — | `uv add --dev ruff` |
| golangci-lint | — | — | — | `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest` |

---

## Sync Mode — `/harness-sync`

### Step 1: Read Existing Harness

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from harness_io import read_harness_files
import json
print(json.dumps(read_harness_files('.claude/harness'), default=str))
"
```

### Step 2: Re-detect Stack

Run `detect_stack('.')` as in setup mode Step 1.

### Step 3: Web Search — Changed Items Only

Compare detected frameworks/linters against those in existing harness files. Only re-search for items that differ or are newly detected.

### Step 4: Diff-Update Harness Files

For each harness file:
1. **Preserve** `## Anti-Pattern Gate` section verbatim
2. **Regenerate** `## Purpose`, `## Core Rules`, `## Pattern Examples` from new web search results
3. Update `updated:` frontmatter field to today's date

Pass the full old harness content + new web search results to yourself and write only changed sections.

---

## Audit Mode — `/harness-audit`

### Step 1: Load Harness Files

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from harness_io import read_all_harness_content
print(read_all_harness_content('.claude/harness'))
"
```

### Step 2: Determine Target Files

- If the user specified files in the command: use those
- If invoked from a stop hook reminder (system message lists changed files): use those
- Otherwise: ask — "Which files should I audit? (e.g., 'src/components/*.tsx', 'recently changed files')"

### Step 3: Audit and Report

For each target file, match against harness domains via `file_patterns`. Report:

```
## Audit Report: <filename>

**Domain**: <matched harness domain>

### Violations

| Severity | Location | Rule Violated | Suggestion |
|---|---|---|---|
| error | line 42 | <rule from ## Core Rules> | <specific fix> |
| warning | line 15 | <rule from ## Core Rules> | <specific fix> |

### Summary
<1-2 sentences overall assessment>
```

If no violations: "✓ No harness violations found in `<filename>`."
