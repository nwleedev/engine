# session-memory

Codex CLI session memory for incremental context summaries. Companion to the
Claude artifact at `plugins/claude/session-memory/`, but independent with no
shared code.

**Verified Codex version:** 0.128.0

## Install

```
codex plugin marketplace add /path/to/this/repo
```

Restart Codex, open `/plugins`, choose the `Engine` marketplace, and install
or enable `session-memory`.

This plugin is skill-first and user-invoked. It does not install automatic
Codex lifecycle hooks.

Available skills:

- `$session-memory:install`
- `$session-memory:checkpoint`
- `$session-memory:resume`
- `$session-memory:status`

## Skills

Codex shows plugin-bundled skills with the plugin namespace. `/plugins` lists
the plugin itself (`session-memory`); use the names below when invoking a
skill from chat.

| Skill | What it does | LLM calls |
|---|---|---|
| `$session-memory:install` | Print AGENTS.md setup guidance for skill-first session memory | 0 |
| `$session-memory:checkpoint` | Prepare and verify context checkpoint handoff | 0 |
| `$session-memory:resume [prefix]` | List or load a prior session's INDEX | 0 |
| `$session-memory:status` | Show pending turns, context count, paths | 0 |

## Compaction recovery

Compaction recovery is driven by AGENTS.md instructions, not a runtime hook. After
manual or automatic context compaction in the same Codex session, the first
action should be invoking `$session-memory:resume <prefix>` with the
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
<root>/.codex/session-memory/threads/<CODEX_THREAD_ID>/
├── INDEX.md
└── contexts/CONTEXT-YYYYMMDD-HH00-checkpoint.md
```

The same JSONL transcript at `~/.codex/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl` is read incrementally on each checkpoint.

New checkpoints use the flat artifact store under `.codex/session-memory/threads`.
Legacy `.codex/sessions/<thread>/contexts` and
`.codex/sessions/_children/<thread>/contexts` files remain readable for
compatibility. `_children` is deprecated: new checkpoints do not create it, and
the only supported uses are legacy reads and migration input.

Subagent and review sessions are still detected as child sessions through the
Codex graph. In normal child-session use, run:

```
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare --role child
```

Use `--parent` only when automatic resolution cannot find the parent, or when
you need to override it explicitly:

```
python3 /path/to/session-memory/skills/checkpoint/checkpoint.py prepare --role child --parent <parent-session-id>
```

Flat `INDEX.md` frontmatter records checkpoint metadata such as `session_id`,
`last_processed_offset`, and `last_updated`; it does not store `role` or
`parent_session_id` as relationship source-of-truth fields. Parent-child
relationships come from the Codex graph when available, or from
`parent_locator` / `graph_store` diagnostics when the graph is degraded. New
checkpoints therefore do not create `_children` paths or parent `Child Sessions`
links.

## Graph degraded mode

The flat artifact is the durable recovery unit even when graph data is
unavailable. In degraded mode:

- `$codex-session-memory:status` can print `Graph: unavailable`.
- `$codex-session-memory:resume <prefix>` resumes from the selected flat
  `.codex/session-memory/threads/<id>/INDEX.md` and recent `contexts/`.
- Checkpoint CONTEXT files still preserve graph diagnostics in `graph_context`,
  including `unavailable`, `source`, `confidence`, `reason`, and `warnings`
  fields when the helper can determine them.

Checkpoint context is not reduced to a smaller summary in this model. The
required 9-section CONTEXT template preserves `executive_summary`,
`detailed_state`, `next_actions`, `graph_context`, and the other handoff
sections so compaction recovery has both the concise state and the detailed
working context.

## Child session checkpoints

Overall parent decision order is:

1. `--parent <thread-id>`
2. `CODEX_SESSION_PARENT_ID`
3. automatic detector

Within automatic detection, the helper reads rollout `session_meta` before state
DB. If rollout metadata identifies a child but lacks parent id, the helper still
checks state DB for a matching parent edge before failing closed. State DB
fallback checks `thread_spawn_edges` first, then `threads.source`.

State DB fallback is a read-only internal fallback. Candidate homes are checked
in this order: explicit `sqlite_home` argument, `CODEX_SQLITE_HOME`, Codex
`config.toml` `sqlite_home`, project `.codex`, then user `~/.codex`.

If child evidence is detected but no parent id can be resolved, the helper exits
with code 2 instead of emitting a top-level main session target.

`INDEX.md` is append-only. If multiple checkpoints update the same HH00 context
file, append a new INDEX entry instead of replacing the previous line. Resume
keeps INDEX event order but deduplicates context file injection by filename to
avoid spending context budget on the same file more than once.

## How session continuity works

`CODEX_THREAD_ID` stays stable across resumed Codex CLI sessions — verified empirically. Multi-day work on the same Codex session accumulates into the same `<root>/.codex/session-memory/threads/<id>/INDEX.md`.

## Legacy child session migration

Use the migration helper for legacy session-memory artifacts that still live
under `.codex/sessions`: legacy main sessions, top-level child sessions, and
legacy `.codex/sessions/_children/<id>` child sessions.

Dry-run first:

```bash
python3 plugins/codex/session-memory/scripts/migrate_child_sessions.py --root /path/to/project
```

Apply after reviewing the planned moves:

```bash
python3 plugins/codex/session-memory/scripts/migrate_child_sessions.py --root /path/to/project --apply
```

The helper moves each source to
`.codex/session-memory/threads/<id>/`, preflights destination conflicts and
duplicate destinations, and strips relationship frontmatter fields such as
`role` and `parent_session_id` from the destination `INDEX.md`. When it finds
synthetic legacy parent links to `_children`, it removes those broken links but
does not add new parent `Child Sessions` links. Failed apply runs roll back on a
best-effort basis; if rollback cannot restore a file, the helper prints a manual
cleanup diagnostic.

## Development

Canonical source lives in the repository source tree. Generated plugin artifacts
live under the runtime session-memory plugin directory. After changing
canonical README, skill, or script files, run:

```bash
rtk python tools/build_plugins.py
rtk python tools/validate_generated.py
```

## Tests

```
python -m pytest tests/codex-session-memory -q
```
