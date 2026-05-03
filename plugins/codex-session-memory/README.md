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

This plugin is skill-first and user-invoked. It does not install automatic
Codex lifecycle hooks.

Available skills:

- `$codex-session-memory:install`
- `$codex-session-memory:checkpoint`
- `$codex-session-memory:resume`
- `$codex-session-memory:status`

## Skills

Codex shows plugin-bundled skills with the plugin namespace. `/plugins` lists
the plugin itself (`codex-session-memory`); use the names below when invoking a
skill from chat.

| Skill | What it does | LLM calls |
|---|---|---|
| `$codex-session-memory:install` | Print AGENTS.md setup guidance for skill-first session memory | 0 |
| `$codex-session-memory:checkpoint` | Prepare and verify context checkpoint handoff | 0 |
| `$codex-session-memory:resume [prefix]` | List or load a prior session's INDEX | 0 |
| `$codex-session-memory:status` | Show pending turns, context count, paths | 0 |

## Compaction recovery

Compaction recovery is driven by AGENTS.md instructions, not a runtime hook. After
manual or automatic context compaction in the same Codex session, the first
action should be invoking `$codex-session-memory:resume <prefix>` with the
current session prefix so Codex reloads the saved handoff before doing more
work.

## Project root resolution (monorepo guard)

Scripts walk up from cwd to find the project root in priority:

1. `CODEX_PROJECT_DIR` env var
2. `<ancestor>/.env` line `CODEX_PROJECT_DIR=...`
3. `git rev-parse --show-toplevel`
4. Topmost ancestor containing `AGENTS.md`
5. Topmost ancestor containing `.codex/`
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
