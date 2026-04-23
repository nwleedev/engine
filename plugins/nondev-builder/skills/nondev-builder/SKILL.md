---
name: "nondev-builder"
description: "Builds professional-grade domain environments through a structured brainstorming dialogue, then generates three artifact files: skill.md, rubric.md, and command.md."
---

# nondev-builder Skill

This skill is invoked by `/nondev-setup` and `/nondev-sync`. It builds a professional-grade
domain environment through a brainstorming-style dialogue loop, then generates three artifact files.

---

## Invocation Detection

Detect the mode from the invoking command and argument:

- `/nondev-setup` (no arg) → **auto-detect mode**: run project_reader to infer domain
- `/nondev-setup <slug>` (hyphenated, no spaces) → **slug mode**: use argument directly as task-name
- `/nondev-setup <description>` (contains spaces) → **natural-language mode**: extract intent, propose 2-3 task-name candidates
- `/nondev-sync <task-name>` → **sync mode**: refresh regenerable sections only (see Sync Rules below)

---

## Step 1: Determine task-name

### Auto-detect mode

Read `README.md`, `CLAUDE.md`, and run `git log -10 --oneline` from the project root.
Present inferred domain to user and ask for confirmation before proceeding.
If no project files are readable, ask the user to describe their domain directly.

### Slug mode

Use the argument as task-name. Validate: lowercase, hyphen-separated, no spaces, not empty.

### Natural-language mode

1. Extract the core intent from the description.
2. Propose exactly 2-3 task-name candidates as a numbered list:
   ```
   Proposed task names:
   1. <candidate-1>
   2. <candidate-2>
   3. <candidate-3>
   Enter 1/2/3 or type a custom name:
   ```
3. Wait for user selection. Confirm the chosen name before proceeding.

**task-name rules**: lowercase, hyphen-separated English, immediately descriptive
(`market-research`, `stock-analysis`, `prd-writing`).
Prohibited: abbreviations (`mr`), numbers (`domain1`), vague terms (`analysis`).

---

## Step 2: Check for existing domain

If `.claude/nondev/<task-name>/skill.md` already exists:

- Ask: "Domain `<task-name>` already exists. Overwrite? (y/n)"
- If n: stop.
- If y: proceed (overwrite on write).

---

## Step 3: Brainstorming loop

Ask exactly **one question per turn** from this checklist. Do not proceed to the next question
until the user answers. If the user's answer covers multiple checklist items, mark all covered items complete — the one-question rule constrains what you ask, not how much the user answers. Do not generate artifacts until all 6 items are complete.

Checklist (track completion internally):

- [ ] **Work goal**: What does this task aim to achieve? (1-2 sentences)
- [ ] **Success criteria**: Describe 2-3 conditions that make an output "good"
- [ ] **Key questions**: What must be answered during this work? (3-5 questions)
- [ ] **Source strategy**: What types of external data are needed? (e.g., industry reports, academic papers, financial filings)
- [ ] **Anti-patterns**: What are common mistakes in this domain?
- [ ] **Violation criteria**: What should the stop hook detect as a quality failure?

After all 6 are complete, summarize the collected answers and ask: "Ready to generate files? (y/n)"

---

## Step 4: Web search (parallel when both available)

Run in parallel when Tavily and Context7 are both available:

**Tavily search** (3 queries):

1. `"<task-name> professional standards best practices"`
2. `"<task-name> common mistakes anti-patterns"`
3. `"<task-name> methodology framework step-by-step"`

**Context7 search** (if official methodology docs exist):

1. Resolve library ID for any official methodology body
2. Query for core framework and working principles

Fallback chain if tools unavailable: WebSearch → WebFetch → training knowledge.
If training data only: append "(training data — may not reflect current information)".

Merge: official docs take precedence; community sources fill gaps.

---

## Step 5: Generate three artifact files

Use brainstorming answers (Step 3) and web search results (Step 4) to generate:

### 5a. `.claude/nondev/<task-name>/skill.md`

```markdown
---
name: <task-name>
description: <description_of_the_task>
task_name: <task-name>
display_name: <display_name>
domain_type: document
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Display Name> Expert Methodology

## Purpose

<Work goal from brainstorming>

## Core Framework

<Analytical structure from web search — 10-year professional standards>

## Working Principles

- [ ] <Principle 1 sourced from web search>
- [ ] <Principle 2 sourced from web search>
- [ ] <Principle 3 sourced from web search>

## Good Example / Bad Example

<Good>
<Correct output example from official methodology guides>
</Good>
<Bad>
<Incorrect output example>
</Bad>

## Source Collection Strategy

<External data types confirmed during brainstorming>

## Custom Examples

<!-- User-added section — preserved on /nondev-sync -->
```

Completeness check before writing: no section is empty.
If web search returned nothing for `## Core Framework`, run a second Tavily query before writing.

### 5b. `.claude/nondev/<task-name>/rubric.md`

```markdown
---
task_name: <task-name>
domain_type: document
---

# <Display Name> Evaluation Rubric

## Violation Criteria

| id  | Violation Type | Detection Question |
| --- | -------------- | ------------------ |

<At least 2 rows from brainstorming violation criteria + web search anti-patterns>

## Anti-Pattern Gate

    <Anti-pattern 1>  →  <Corrective action>
    <Anti-pattern 2>  →  <Corrective action>

## Pass Criteria

- 0 violations: PASS
- 1-2 violations: WARN (propose fix, resubmit once)
- 3+ violations: FAIL (rework required)
```

Completeness check: `## Violation Criteria` table must have ≥ 2 rows.

### 5c. `.claude/commands/<task-name>.md`

```markdown
---
description: <Display Name> professional workflow — parallel research + independent evaluation
---

# <Display Name> Workflow

Execute the following steps in order. Argument: $ARGUMENTS

## Step 1: Load Methodology (B Layer)

Read `.claude/nondev/<task-name>/skill.md` and apply it as the working context.
All output must follow its principles.

## Step 2: Parallel Research (A Layer)

Spawn 3 subagents in parallel:

**Researcher-1** (primary data):

- Tools: WebSearch, WebFetch (Tavily preferred)
- Goal: Figures and authoritative sources for "$ARGUMENTS"
- Return: { data: [...], sources: [{title, url, date, org}] }

**Researcher-2** (comparative analysis):

- Tools: WebSearch, WebFetch
- Goal: 3+ subjects, 3+ evaluation axes
- Return: { items: [...], criteria: [...], sources: [...] }

**Researcher-3** (trends):

- Tools: WebSearch, WebFetch
- Goal: Industry reports from the past 12 months
- Return: { trends: [...], sources: [...] }

Synthesize: deduplicate sources, cross-validate figures.

## Step 3: Produce Analysis

Use methodology (Step 1) and sourced data (Step 2). Cite every figure inline with source.

## Step 4: Independent Evaluation (C Layer)

Read `.claude/nondev/<task-name>/rubric.md` and pass to evaluator subagent:

**Evaluator** (isolated context — no self-review bias):

- Input: rubric violation criteria + Step 3 analysis
- Tools: none
- Return: { violations: [{id, location, description}], passed: bool }

violations present → revise, re-evaluate once (limit: 1 retry)
violations absent → final output
```

---

## Step 6: Upsert index.json

After all three files are written, update `.claude/nondev/index.json`:

```json
{
  "task_name": "<task-name>",
  "display_name": "<display_name>",
  "command": "/<task-name>",
  "keywords": {
    "ko": ["<5-8 Korean keywords from brainstorming + web search>"],
    "en": ["<5-8 English keywords>"]
  }
}
```

Run the following Bash command to write the entry (replace placeholder values with actual computed values):

```bash
python3 - <<'EOF'
import sys, os
plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
if not plugin_root:
    raise SystemExit("CLAUDE_PLUGIN_ROOT not set")
sys.path.insert(0, os.path.join(plugin_root, "scripts"))
from nondev_io import upsert_domain

# SET THESE VARIABLES — replace each value with the computed result from Steps 1-4
task_name    = "<task-name>"       # e.g. "market-research"
display_name = "<display-name>"   # e.g. "Market Research"
ko_keywords  = ["<kw1>", "<kw2>", "<kw3>", "<kw4>", "<kw5>"]
en_keywords  = ["<kw1>", "<kw2>", "<kw3>", "<kw4>", "<kw5>"]
# END OF VARIABLES

upsert_domain(os.getcwd(), {
    "task_name": task_name,
    "display_name": display_name,
    "command": f"/{task_name}",
    "keywords": {"ko": ko_keywords, "en": en_keywords}
})
print("index.json updated")
EOF
```

This uses the file-locking `upsert_domain` for multi-terminal safety.

---

## Step 7: Final completeness verification

Before reporting success, verify:

- [ ] `skill.md`: no section is empty; `## Core Framework` has content
- [ ] `rubric.md`: `## Violation Criteria` has ≥ 2 rows
- [ ] `index.json`: domain entry present with ≥ 3 keywords in each of ko and en
- [ ] `commands/<task-name>.md`: exists and has all 4 steps

Report the three file paths and remind the user to run `/<task-name> [goal]` to start.

---

## Sync Rules (`/nondev-sync <task-name>`)

If `<task-name>` argument is absent, stop and reply: "Usage: `/nondev-sync <task-name>` — provide an existing domain name. Run `/nondev-setup` to create a new domain."

Before syncing, verify `.claude/nondev/<task-name>/skill.md` exists.
If it does not exist, stop and reply: "Domain `<task-name>` not found. Run `/nondev-setup <task-name>` first."

When invoked via `/nondev-sync`:

- **Regenerate** (via fresh web search): `## Core Framework`, `## Working Principles`, `## Good Example / Bad Example`
- **Preserve** (user-edited): `## Source Collection Strategy`, `## Custom Examples`
- **Do not touch**: `.claude/commands/<task-name>.md` (sync never modifies command files)
- Update `updated:` frontmatter date after regeneration
