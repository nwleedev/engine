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
| **Frontend Developers** | React/Next.js web apps, UI component libraries | [Quick Start](.claude/docs/GETTING-STARTED.md#41-개발-프로젝트-프론트엔드) |
| **Backend Developers** | FastAPI REST API, Go microservices | [Quick Start](.claude/docs/GETTING-STARTED.md#42-개발-프로젝트-백엔드-python) |
| **Researchers** | Market research, competitor analysis, tech trends | [Quick Start](.claude/docs/GETTING-STARTED.md#43-시장-조사-프로젝트) |
| **Marketers** | Campaign planning, A/B test design, ad copy | [Quick Start](.claude/docs/GETTING-STARTED.md#44-마케팅-프로젝트) |
| **Architects** | System architecture docs, RFCs, ADRs | [Quick Start](.claude/docs/GETTING-STARTED.md#45-설계-문서-프로젝트) |
| **Learners** | Kubernetes intro, React learning, ML basics | [Quick Start](.claude/docs/GETTING-STARTED.md#46-학습-프로젝트) |

---

## Installation

### Method 1: Plugin Install (Recommended)

> Install as a Claude Code plugin without copying files to your project.

```bash
claude plugin install nwleedev/engine
```

For per-project settings, create `.claude/engine.env` (optional):

```bash
# .claude/engine.env
REVIEW_AGENTS="domain,structure"         # Review perspectives (comma-separated)
RESEARCH_PERSPECTIVES="pro,con"          # Research perspectives (comma-separated)
```

### Method 2: Standalone Install

> Copies all files to your project's `.claude/` directory.

```bash
# Install harness to project (one-liner, no git needed)
sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- ~/my-project

# Run Claude Code
cd ~/my-project && claude
```

Update: `bash .claude/scripts/update.sh` or re-run the same command.

<details>
<summary>Manual install (using git)</summary>

```bash
git clone https://github.com/nwleedev/engine.git /tmp/engine
/tmp/engine/.claude/scripts/bootstrap.sh --source /tmp/engine --target ~/my-project
rm -rf /tmp/engine
cd ~/my-project && claude
```
</details>

### Comparison

| Item | Plugin | Standalone |
|------|--------|-----------|
| Install | `claude plugin install` | curl one-liner |
| Update | Automatic (plugin manager) | `update.sh` manual |
| Multiple projects | One install, shared | Install per project |
| Customization | `.claude/engine.env` | `.claude/settings.local.json` |
| Skill prefix | `/engine:deep-study` | `/deep-study` |

Prerequisites: Claude Code CLI. Standalone install additionally requires curl, tar, jq. See [Getting Started](.claude/docs/GETTING-STARTED.md#1-사전-준비) for detailed setup.

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

### Scripts (Automation)

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Install harness environment to new project |
| `sync.sh` | Sync core repository updates to project |
| `promote.sh` | Promote project harness to core repository |
| `check-plan.sh` | Block editing without plan (hook) |
| `check-plan-review.sh` | Plan quality validation (hook) |
| `suggest-harness.sh` | Auto-suggest harness based on file content (hook) |
| `track-edits.sh` | Track edit count, trigger reviewer (hook) |
| `snapshot.sh` | Save session snapshot (hook) |
| `update.sh` | Update installed harness to latest engine version |
| `migrate.sh` | v1→v2 migration |

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
| [Getting Started](.claude/docs/GETTING-STARTED.md) | Install, daily usage, customization, troubleshooting, architecture |
| [Migration Guide](.claude/docs/MIGRATION.md) | v1→v2 migration guide |
| [CLAUDE.md](CLAUDE.md) | Project rules (file read by Claude) |
| [CLAUDE.md.example](.claude/CLAUDE.md.example) | CLAUDE.md template for new projects |

---

## Project Structure

```
.claude/
  engine.env          # Plugin settings (optional, review/research perspectives, etc.)
  settings.json          # Hook settings (system-managed, no editing needed)
  settings.local.json    # Per-project permission/hook customization
  scripts/               # 9 automation scripts
  skills/                # 6 skills + harness-engine subsystem
  agents/                # 6 specialized agents
  docs/                  # Getting Started, Migration
  plans/                 # Work plans (auto-generated)
  sessions/              # Session snapshots (auto-generated)
```

Only **3 files** need direct editing: `CLAUDE.md` (project rules), `.claude/settings.local.json` (permissions), `.claude/engine.env` (plugin settings, optional).

---

## Updates and Sync

### Method 1: Direct Update from Project (Recommended)

```bash
# Check for updates only
bash .claude/scripts/update.sh --check

# Preview changes
bash .claude/scripts/update.sh --dry-run

# Run update
bash .claude/scripts/update.sh

# Offline update from local engine repo
bash .claude/scripts/update.sh --source ~/engine

# Update to specific version
bash .claude/scripts/update.sh --version v1.2.0
```

### Method 2: Re-run install.sh

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- ~/my-project
```

What updates manage: hook scripts, settings.json, generic skills, agents, CLAUDE.md core sections.
What updates don't touch: project rules, domain harnesses, session/plan data, settings.local.json.

---

## Commit Convention

```
<type>(<scope>): <subject>
```

type: `feat`, `fix`, `refactor`, `docs`, `chore`, etc.
