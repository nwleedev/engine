# codex-session-memory

Codex CLI session memory for incremental context summaries. Companion to
`plugins/session-memory/` (Claude Code), but independent with no shared code.

**Verified Codex version:** 0.128.0

## Install

```
codex plugin marketplace add /path/to/this/repo
```

Restart Codex, open `/plugins`, choose the `Engine` marketplace, and install
or enable `codex-session-memory`.

Manual skills work after installation. Automatic mode requires the Codex hooks
feature flag below.

## Automatic mode

Enable Codex hooks in Codex config:

```toml
[features]
codex_hooks = true
```

The plugin uses `SessionStart` for compact context injection and `Stop` for
policy-gated automatic checkpoints. `PostToolUse` marks evidence that helps
the stop hook decide whether a checkpoint is useful. Manual skills remain
available:

- `$codex-session-memory:checkpoint`
- `$codex-session-memory:resume`
- `$codex-session-memory:status`

## Skills

Codex shows plugin-bundled skills with the plugin namespace. `/plugins` lists
the plugin itself (`codex-session-memory`); use the names below when invoking a
skill from chat.

| Skill | What it does | LLM calls |
|---|---|---|
| `$codex-session-memory:checkpoint` | Save delta turns as a context summary | 1 (codex-exec, ~15-60s) |
| `$codex-session-memory:resume [prefix]` | List or load a prior session's INDEX | 0 |
| `$codex-session-memory:status` | Show pending turns, context count, paths | 0 |

## Project root resolution (monorepo guard)

Scripts walk up from cwd to find the project root in priority:

1. `CODEX_PROJECT_DIR` env var
2. `<ancestor>/.env` line `CODEX_PROJECT_DIR=...`
3. Topmost ancestor containing `AGENTS.md`
4. Topmost ancestor containing `.codex/`
5. `git rev-parse --show-toplevel`
6. cwd

If the resolved root differs from `git rev-parse --show-toplevel` and no env override is set, the plugin **refuses to write** (loud failure beats silent data fragmentation).

### Monorepo recommendation

Add to `<root>/.env`:

```
CODEX_PROJECT_DIR=/abs/path/to/monorepo/root
```

Confirm `.env` is in `.gitignore` before committing other changes.

## Data layout

```
<root>/.codex/sessions/<CODEX_THREAD_ID>/
├── INDEX.md
└── contexts/CONTEXT-YYYYMMDD-HHMM-<title>.md
```

The same JSONL transcript at `~/.codex/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl` is read incrementally on each checkpoint.

## How session continuity works

`CODEX_THREAD_ID` stays stable across `codex exec resume <id>` — verified empirically. Multi-day work on the same Codex session accumulates into the same `<root>/.codex/sessions/<id>/INDEX.md`.

## Tests

```
python -m pytest tests/codex-session-memory -q
```
