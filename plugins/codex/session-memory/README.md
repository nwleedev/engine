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

| Skill                             | What it does                                                  | LLM calls |
| --------------------------------- | ------------------------------------------------------------- | --------- |
| `$session-memory:install`         | Print AGENTS.md setup guidance for skill-first session memory | 0         |
| `$session-memory:checkpoint`      | Prepare and verify context checkpoint handoff                 | 0         |
| `$session-memory:resume [prefix]` | List or load a prior session's INDEX                          | 0         |
| `$session-memory:status`          | Show pending turns, context count, paths                      | 0         |

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
<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/
├── INDEX.md
└── contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md
```

The same JSONL transcript at `~/.codex/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl`
is read incrementally on each checkpoint. `CODEX_THREAD_ID` is only used for
that transcript lookup. New checkpoint artifacts are written only under:

```
.codex/session-memory/threads/<CODEX_SESSION_ID>/
```

Set `CODEX_SESSION_ID` to the main session id before starting or resuming
Codex. Inline env is preferred over a checked-in `.env` file:

```
CODEX_SESSION_ID=<main-thread-id> codex resume <main-thread-id>
```

Flat `INDEX.md` frontmatter records checkpoint metadata such as `session_id`,
`source_thread_id`, `last_processed_offset`, and `last_updated`; it does not
store `role` or `parent_session_id` as relationship source-of-truth fields. If
`CODEX_THREAD_ID` differs from `CODEX_SESSION_ID`, checkpoint prints a
non-blocking warning and still writes to the `CODEX_SESSION_ID` artifact. A
wrong `CODEX_SESSION_ID` can contaminate another session artifact, so treat it
as an explicit storage target.

Legacy `.codex/sessions/<thread>/contexts` and
`.codex/sessions/_children/<thread>/contexts` files remain readable for
compatibility. `_children` is deprecated: new checkpoints do not create it, and
the only supported use is legacy read compatibility.

## Artifact-only mode

The flat artifact is the durable recovery unit. Session-memory does not read
Codex sqlite state DBs, `thread_spawn_edges`, `threads.source`, rollout
`session_meta`, or parent/child graph helpers in checkpoint, resume, or status.
In artifact-only mode:

- `$session-memory:status` reports only the current `CODEX_SESSION_ID` artifact.
- `$session-memory:resume <prefix>` resumes from the selected
  `.codex/session-memory/threads/<id>/INDEX.md` and recent `contexts/`.
- Checkpoint CONTEXT files keep `graph_context` as a compatibility section, but
  it records that graph and parent discovery were not used.
- If `INDEX.md` update fails after writing a context file, the context is kept
  and the helper prints the context path, backup path when available, and manual
  repair guidance.

Checkpoint context is not reduced to a smaller summary in this model. The
required 9-section CONTEXT template preserves `executive_summary`,
`detailed_state`, `next_actions`, `graph_context`, and the other handoff
sections so compaction recovery has both the concise state and the detailed
working context.

## Concurrent checkpoints

Context files are created as
`contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md`. `source_thread_id` is stored
inside the context metadata rather than the filename. `INDEX.md` updates take an
`INDEX.md.lock`, reread the latest file under the lock, create writer-scoped
backup/temp files in the same directory, fsync the temp file, and use
`os.replace` for the final update.

## How session continuity works

`CODEX_SESSION_ID` is the explicit session-memory artifact id. Multi-day work
on the same Codex session accumulates into the same
`<root>/.codex/session-memory/threads/<id>/INDEX.md` only when you keep passing
the same `CODEX_SESSION_ID`.

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
python -m pytest tests/session-memory -q
```
