---
description: Print a settings.local.json snippet to pin CLAUDE_PROJECT_DIR for this project
argument-hint: "[path]"
---

# Bind Project Root

Resolve the canonical project root and print a copy-pasteable JSON snippet for
`<root>/.claude/settings.local.json`. No files are modified.

`$ARGUMENTS` is an optional absolute path. If omitted, the root is auto-detected
(walk topmost `.claude/` ancestor under `$HOME` → git toplevel → cwd).

```bash
ARG="${ARGUMENTS:-}"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bind.py" $ARG
```

After pasting the snippet into `settings.local.json`, exit Claude completely and
relaunch. The `env` block is injected into hook subprocesses at session start.
