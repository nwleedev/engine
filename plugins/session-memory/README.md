# session-memory

Per-session context narration with explicit, isolated resume. Each Claude Code session writes its own `INDEX.md` as you work, and you choose which prior session to resume — sessions never cross-pollinate automatically.

## How it works

session-memory runs four hooks:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Every session open | Source-based dispatch: `startup` injects only `INSIGHT.md` (project-wide highlights), `resume` re-injects this session's `INDEX.md`, `compact` re-injects recent contexts, `clear` injects nothing. Capped at 8KB. |
| `Stop` | End of each turn | Narration gate: only narrates if transcript delta ≥1KB, hasn't exceeded 60KB hard cap, and ≥300s since last narration. Forces Haiku 4.5; falls back after 3 consecutive failures. |
| `PreToolUse` | Before each tool call | Mid-turn checkpoint using the same gate, so long turns still produce narrations. |
| `SessionEnd` | Session ends | Forces a final narration regardless of thresholds. |

`PreCompact` and `UserPromptSubmit` from v1 are removed — `PreCompact` had a macOS bug and no `additionalContext` support, and `SessionStart` with `source="compact"` covers the post-compact handoff.

### Isolation

Each `session_id` is fully isolated. `SessionStart` on `startup` does **not** auto-inject other sessions' contexts, so parallel terminals on the same project never bleed state into each other. `find_project_root` prefers the git toplevel, so monorepo sub-packages cannot create their own `.claude/sessions/` directory.

### Storage layout

```
.claude/sessions/
├── INSIGHT.md                       # Project-wide highlights (≤200 entries)
├── INSIGHT-archive-<YYYY-MM>.md     # Rolled-off entries
├── _archive/<YYYY-MM>/<id>.tar.gz   # Sessions older than 30 days
└── <session_id>/
    ├── INDEX.md                     # Session summary with frontmatter
    ├── log.jsonl                    # Per-decision diagnostic log
    └── contexts/
        └── CONTEXT-*.md             # Mid-session checkpoint snapshots
```

Sessions older than 30 days are tar-gzipped into `_archive/<YYYY-MM>/`. `INSIGHT.md` is capped at 200 entries; the oldest 50 roll into `INSIGHT-archive-<YYYY-MM>.md`.

## Slash commands

| Command | Purpose |
|---|---|
| `/session-memory:resume` | Interactive menu of this project's sessions; injects the chosen session's `INDEX.md` |
| `/session-memory:status` | Prints current session stats and recent decisions from `log.jsonl` |
| `/session-memory:checkpoint` | Forces a narration now, regardless of gate thresholds |
| `/session-memory:migrate` | Deduplicates v1 `INDEX.md` entries; supports `--dry-run` and `--apply` |

## Installation

```
/plugin marketplace add nwleedev/session-memory
```

Or install the full engine marketplace (includes all 4 plugins):

```
/plugin marketplace add nwleedev/engine
```

## Usage

The hooks run automatically. There is no trigger keyword.

1. Start a session and work normally. `Stop`/`PreToolUse` periodically narrate progress into `INDEX.md` and `contexts/`.
2. To pick up where a prior session left off, run `/session-memory:resume` and pick from the menu — only the chosen session's context is injected.
3. To force a narration before a risky operation, run `/session-memory:checkpoint`.
4. To inspect what the gate has been deciding, run `/session-memory:status`.

Injected context goes into Claude's system context — you will not see it printed, but Claude uses it when the conversation references prior work.

## Diagnostics

Every narration decision (allowed, skipped, why) is appended to `.claude/sessions/<session_id>/log.jsonl`. `/session-memory:status` reads it. If narrations seem too sparse or too frequent, inspect this log to see which gate (delta, hard cap, time gap, or failure-count fallback) is firing.

## Migrating from v1

If you have existing `.claude/sessions/<id>/INDEX.md` files from session-memory v1, run:

```
/session-memory:migrate --dry-run
/session-memory:migrate --apply
```

This deduplicates legacy entries so the v2 SessionStart injection budget stays under 8KB.
