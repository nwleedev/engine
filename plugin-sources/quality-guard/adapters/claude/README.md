# quality-guard

Detects superficial code changes and vague language via hooks and skills.

## Project Root Resolution

quality-guard writes to `<project-root>/.claude/feedback/...` (e.g., `raw.md`,
`rules.md`). The root is resolved with this priority:

1. `CLAUDE_PROJECT_DIR` env var (set via `.claude/settings.local.json`).
2. Topmost ancestor of cwd containing a `.claude/` directory, bounded by `$HOME`.
3. `git rev-parse --show-toplevel`.
4. cwd itself.

If you launch Claude from a subdirectory of a monorepo, the auto-detection may
pick the wrong root. The recommended remedy lives in the session-memory plugin:
run `/session-memory:bind` to print a JSON snippet for `settings.local.json`.

If session-memory is not installed, paste the following into
`<root>/.claude/settings.local.json` (replacing `<root>` with the absolute path
to your monorepo / project root):

```json
{
  "env": {
    "CLAUDE_PROJECT_DIR": "<root>"
  }
}
```

Then exit Claude and relaunch. The same `CLAUDE_PROJECT_DIR` value is used by
both plugins.
