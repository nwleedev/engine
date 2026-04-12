# Claude Code Harness System

[한국어](README.ko.md)

A configuration/automation framework that installs automatic rules, quality gates, and domain knowledge on Claude Code.

> Not a code library. It's a **configuration layer** that sits on top of Claude Code.

---

## Why?

| Claude Code Default | With Harness |
|---|---|
| Starts coding/writing immediately on request | **Enforces planning** before editing (hooks block) |
| Repeats library anti-patterns | **Auto-suggests domain rules** when files are read |
| Large changes pass without review | 2-4 single review, 5+ **parallel quality review** |
| Context lost after long conversations | **Auto-saves/restores context** on session end/compaction |
| Plan quality is inconsistent | **Auto-validates completeness** when plan finishes |
| Risky git commands possible | **Blocks destructive commands** like `--force`, `reset --hard` |

---

## Who Is This For?

Applies to **all work using Claude Code** — not just coding, but research, marketing, design, learning, and more.

| Audience | Example Projects | Details |
|----------|-----------------|---------|
| **Frontend Developers** | React/Next.js web apps, UI component libraries | [Quick Start](docs/GETTING-STARTED.md#frontend) |
| **Backend Developers** | FastAPI REST API, Go microservices | [Quick Start](docs/GETTING-STARTED.md#backend-python) |
| **Researchers** | Market research, competitor analysis, tech trends | [Quick Start](docs/GETTING-STARTED.md#research) |
| **Learners** | Kubernetes intro, React learning, ML basics | [Quick Start](docs/GETTING-STARTED.md#learning) |

---

## Installation

Distributed as a Claude Code plugin.

```bash
claude plugin marketplace add nwleedev/engine
claude plugin install engine@engine
```

Per-project settings (optional) go in `.claude/engine.env`:

```bash
# .claude/engine.env
WORK_REVIEW_PERSPECTIVES="domain,structure,requirements"
PLAN_REVIEW_PERSPECTIVES="structure,steps,requirements"
RESEARCH_PERSPECTIVES="pro,con"
```

Prerequisites: Claude Code CLI. See [Getting Started](docs/GETTING-STARTED.md#prerequisites) for detailed setup and [DISTRIBUTION.md](DISTRIBUTION.md) for team/organization install options.

---

## System Components

### Hooks (Automatic)

| Hook | Trigger | Action |
|------|---------|--------|
| Plan enforcement | Before file edit | Blocks editing without a plan |
| Plan quality validation | On plan mode exit | Auto-checks file existence, required sections, ambiguity |
| Harness suggestion | After file read | Detects domain keywords in file content → suggests related rules |
| Edit tracking | After file edit | Tracks modified file count; 2-4 single / 5+ parallel review |
| Session snapshot | On session end | Saves work state to `.claude/sessions/` |
| Context restore | On session start/compaction | Restores context from previous snapshots |
| ExitPlanMode review | First ExitPlanMode call | Forces perspective-based plan review before approval |
| Destructive git command block | Before Bash git calls | Blocks `--no-verify`, `--force` push, `reset --hard`, `clean -f`, `branch -D`, `checkout -- .` |

### Skills (Activated on Invocation)

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| harness-engine | `/harness-engine` | Auto-generate project-specific domain rules |
| deep-study | `/deep-study` | Step-by-step learning protocol (assess→design→lecture→verify) |
| failure-response | `/failure-response` | Error response methodology (root cause first) |
| research-methodology | `/research-methodology` | Structured research framework |
| socratic-thinking | `/socratic-thinking` | Critical thinking principles (explore first, verify assumptions) |

### Agents (Auto/Manual)

| Agent | Trigger | Role |
|-------|---------|------|
| work-reviewer | Auto: 2-4 single / 5+ parallel | Change quality review (perspective mode supported) |
| plan-readiness-checker | Auto: on plan exit | Plan executability verification |
| turn-summarizer | Auto: on session end | Narrative turn summary generation |
| domain-professor | Manual: via `/deep-study` | Domain learning professor + feed generation |
| harness-researcher | Internal: `/harness-engine` | Domain research for harness generation |
| project-researcher | Manual | Technology selection, architecture research (perspective mode supported) |

---

## Core Concepts

### Harness Skills

Domain-specific rule files (`.claude/skills/harness-*.md`) that Claude automatically references when working in that domain. Initially empty — invoke `/harness-engine` to analyze your project stack and auto-generate custom rules. Afterwards, hooks suggest the relevant harness whenever related files are read.

### Plan Enforcement

Enforces planning before all editing work. Instead of starting coding or writing immediately, Claude first creates a plan file in `.claude/plans/` and executes only after user approval. Applies equally to non-development work (research, marketing docs, etc.).

### Session Continuity

When conversations get long, Claude Code may compress or lose previous context. This system automatically saves snapshots at session end and compaction points, then auto-restores them on the next session or after compaction. No user action required.

---

## Documentation

| Document | Content |
|----------|---------|
| [Getting Started](docs/GETTING-STARTED.md) | Install, first use, customization, troubleshooting, reference |
| [DISTRIBUTION.md](DISTRIBUTION.md) | Plugin distribution options for individuals, teams, organizations |

---

## Updates

The plugin manager handles updates.

```bash
claude plugin update engine@engine
```

---

## Commit Convention

```
<type>(<scope>): <subject>
```

type: `feat`, `fix`, `refactor`, `docs`, `chore`, etc.
