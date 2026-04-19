# session-memory

Automatic session context narration and injection. At the start of each session, Claude receives a summary of the last 3 sessions as background context — no manual setup required.

## How it works

session-memory runs four hooks:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Every session open | Reads the last 3 session summaries and injects them as context |
| `Stop` | Every session end | Narrates the session and writes a summary to `.claude/sessions/<id>/INDEX.md` |
| `PreToolUse` | Before each tool call | Guards session data from accidental modification |
| `PreCompact` | Before context compaction | Summarizes the current context into a checkpoint file |

Session summaries are stored in `.claude/sessions/<session_id>/`:

```
.claude/sessions/<session_id>/
├── INDEX.md          # Session summary with frontmatter (session_id, timestamps)
└── contexts/
    └── CONTEXT-*.md  # Checkpoint snapshots taken during compaction
```

The most recent session receives its full `INDEX.md` plus up to 3 context snapshots. Older sessions contribute only their `INDEX.md`.

## Installation

```
/plugin marketplace add nwleedev/session-memory
```

Or install the full engine marketplace (includes all 4 plugins):

```
/plugin marketplace add nwleedev/engine
```

## Usage

No commands or trigger keywords. The plugin is fully automatic:

1. Open a Claude Code session and start working normally.
2. When the session ends, Claude narrates what happened and writes `INDEX.md`.
3. On the next session start, Claude silently receives the last 3 summaries as background context.

The injected context appears as part of Claude's system context — you will not see it printed, but Claude uses it when answering questions that reference prior work.
