# engine

4 Claude Code plugins that enforce work quality — session continuity, domain learning, research rigor, and plan adherence. Each plugin can be installed and used independently.

## What is engine?

engine is a Claude Code plugin marketplace that installs four quality-enforcement plugins into your development environment. Together they ensure Claude maintains context across sessions, builds domain expertise on demand, validates research claims before answering, and adheres to project-specific coding standards.

Each plugin can be installed independently — install only what you need.

## Plugins

| Plugin | Description |
|---|---|
| [session-memory](plugins/session-memory/README.md) | Automatically narrates and injects the last 3 session summaries at session start |
| [domain-professor](plugins/domain-professor/README.md) | Generates structured learning materials for any domain on demand |
| [better-research](plugins/better-research/README.md) | Enforces a 5-step research protocol — hypothesis, sources, counter-argument, root cause, answer |
| [harness-engineer](plugins/harness-engineer/README.md) | Injects domain-specific coding standards and detects violations at session end |

## Quick Install

Install all 4 plugins at once:

```
/plugin marketplace add nwleedev/engine
```

## Individual Installation

To install a single plugin, see its README:

- [session-memory](plugins/session-memory/README.md)
- [domain-professor](plugins/domain-professor/README.md)
- [better-research](plugins/better-research/README.md)
- [harness-engineer](plugins/harness-engineer/README.md)

## Requirements

Claude Code with plugin marketplace support.
