# Getting Started

> [한국어](GETTING-STARTED.ko.md)

The engine is distributed as a **Claude Code plugin**. This guide walks through install, first use, and per-project configuration.

## Prerequisites

- Claude Code CLI ([install docs](https://docs.claude.com/en/docs/claude-code))
- A Claude Code session running in a project directory

No other tooling is required. Everything the plugin needs ships with the plugin.

## Install

```bash
claude plugin marketplace add nwleedev/engine
claude plugin install engine@engine
```

Verify:

```bash
claude plugin list
```

You should see `engine` with its skills (`/engine:deep-study`, `/engine:harness-engine`, …) and agents.

Updating and uninstalling are handled by the plugin manager:

```bash
claude plugin update engine@engine
claude plugin uninstall engine@engine
```

### Local development

Contributors working on the plugin itself can point Claude Code at a local checkout:

```bash
claude --plugin-dir ./engine
```

Inside an active session, `/reload-plugins` picks up changes without restarting.

### Team auto-install

Add the marketplace to your project's `.claude/settings.json` so team members are prompted to install on first trust:

```json
{
  "extraKnownMarketplaces": {
    "engine": {
      "source": { "source": "github", "repo": "nwleedev/engine" }
    }
  },
  "enabledPlugins": {
    "engine@engine": true
  }
}
```

See [DISTRIBUTION.md](../DISTRIBUTION.md) for organization-wide managed settings.

## First Use — Planning Workflow

Once the plugin is active, Claude Code behaves differently:

- **Plan mode is enforced before any edit.** Requesting `"implement user auth"` makes Claude write a plan file under `.claude/plans/` first. Plans are reviewed by perspective-specific checkers before you approve them.
- **Domain rules auto-suggest** — once you have harnesses. After `/engine:harness-engine` generates project-specific harness skills under `.claude/skills/harness-*.md`, Claude surfaces the relevant rule set whenever it reads a file matching a skill's `matchPatterns`. Before generating any harnesses, no suggestions fire.
- **Edits are tracked.** A single `work-reviewer` fires once two files are modified. Multi-perspective review fires at five or more files, or when any infrastructure file is touched alongside at least one other file. Thresholds are overridable via `REVIEW_THRESHOLD_SINGLE` / `REVIEW_THRESHOLD_MULTI`.
- **Sessions are snapshot.** `.claude/sessions/<id>/SESSION.md` captures state at session end and before compaction; the next session restores it automatically.
- **Destructive git commands are blocked.** `--no-verify`, `--force` push, `reset --hard`, `clean -f`, `branch -D`, `checkout -- .` all require explicit override.

None of these need configuration to work. Just install and use Claude Code normally.

## Per-Project Configuration

Create `.claude/engine.env` in your project to override review/research defaults:

```bash
# .claude/engine.env
WORK_REVIEW_PERSPECTIVES="domain,structure,requirements"
PLAN_REVIEW_PERSPECTIVES="structure,steps,requirements"
RESEARCH_PERSPECTIVES="pro,con"
REVIEW_THRESHOLD_SINGLE=2
REVIEW_THRESHOLD_MULTI=5
```

All variables are optional; the plugin ships with sensible defaults documented in `engine.env.example`.

A template ships with the plugin; copy and edit to taste.

Project-specific permissions, additional hooks, and custom agents live in `.claude/settings.json` and `.claude/settings.local.json`. These are merged with the plugin's hooks at runtime — nothing the plugin ships needs to be edited directly.

## Generate Domain Rules

`/harness-engine` analyzes your stack and generates harness skills tailored to it:

```
/engine:harness-engine
> Create harnesses for our FastAPI + SQLAlchemy backend
```

The generated skills live at `.claude/skills/harness-*.md` under your project (outside the plugin), so they travel with the repo. Each skill declares `matchPatterns` so the auto-suggest hook can route the right rules when related files are read.

## Quick Starts by Audience

### Frontend

```
/engine:harness-engine
> Generate harnesses for React + TanStack Query + Zustand
```

### Backend (Python)

```
/engine:harness-engine
> Generate harnesses for FastAPI + SQLAlchemy 2.0
```

### Research

```
> Research the Korean B2B SaaS market size and top players
```

Planning is enforced identically — Claude scopes the research and cites sources before writing.

### Learning

```
/engine:deep-study
> Teach me Kubernetes from fundamentals
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "No plan files found" error blocks editing | Expected behavior | Enter plan mode (Shift+Tab) or type `/plan` |
| Harness suggestions don't appear | `matchPatterns` missing or `fileGlob` doesn't match | Check the skill frontmatter; description keywords act as a fallback |
| Session restore didn't trigger | `.claude/sessions/` missing | `mkdir -p .claude/sessions` |
| work-reviewer didn't fire | Fewer than 2 files modified | Expected — triggers start at 2 files |
| multi-review didn't fire | Fewer than 5 files and no infra change | Expected — triggers at 5+ or infra paths |

## FAQ

**Q. Do I still need to install anything into `.claude/`?**
No. The plugin is self-contained. The only files you add to `.claude/` are the ones *you* want — `engine.env` for overrides, `settings.local.json` for permissions, your own project-specific skills or agents.

**Q. How do I turn off plan enforcement?**
Not recommended, but you can add an override to `.claude/settings.local.json` that suppresses the plan hook for specific matchers. The default exists because plan-less edits lose direction fast.

**Q. What if the plugin conflicts with another one?**
Plugin skills are namespaced (`/engine:<skill>`). Agents are also namespaced (`engine:<agent>`). Conflicts with other plugins are avoided by design.

**Q. How do I share harnesses across projects?**
Commit `.claude/skills/harness-*.md` to your project repo. They live outside the plugin and travel with the codebase.

## Reference: Skills and Agents

| Skill | Invocation | Purpose |
|---|---|---|
| setup | `/engine:setup` | Initialize `CLAUDE.md` and `engine.env` from plugin templates |
| harness-engine | `/engine:harness-engine` | Generate project-specific domain rules |
| deep-study | `/engine:deep-study` | Step-by-step learning protocol |
| failure-response | `/engine:failure-response` | Error-handling methodology |
| research-methodology | `/engine:research-methodology` | Structured research framework |
| socratic-thinking | `/engine:socratic-thinking` | Critical-thinking principles |

| Agent | Trigger | Role |
|---|---|---|
| work-reviewer | Auto on edit-count / infra thresholds | Change-quality review (single or perspective-parallel) |
| plan-readiness-checker | Auto on plan exit | Plan executability verification |
| turn-summarizer | Auto on session end | Narrative turn summary |
| domain-professor | `/engine:deep-study` | Domain learning |
| harness-researcher | `/engine:harness-engine` | Domain research for harness generation |
| project-researcher | Manual via dispatch | Technology/architecture research |

---

See [README](../README.md) for an overview of why this exists and [DISTRIBUTION.md](../DISTRIBUTION.md) for distribution options.
