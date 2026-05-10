---
description: Migrate v1 session-memory data to v2 (dedup INDEX entries)
argument-hint: "[--dry-run | --apply]"
---

# Session Memory v1 → v2 Migration

`$ARGUMENTS` selects mode. Default: `--dry-run`.

## Steps

1. Determine project root: `git rev-parse --show-toplevel || pwd`.
2. Run the migration script via Bash:

```bash
MODE="${ARGUMENTS:---dry-run}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DRY=true
[ "$MODE" = "--apply" ] && DRY=false

python3 - <<PY
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.join("$ROOT", "plugins", "session-memory", "scripts"))
import migrate
sessions = Path("$ROOT") / ".claude" / "sessions"
result = migrate.dedup_all_sessions(sessions, dry_run=$([[ $DRY = true ]] && echo True || echo False))
changed = [s for s, c in result.items() if c]
total = len(result)
print(json.dumps({"mode": "$MODE", "total_sessions": total, "changed": changed}, indent=2, ensure_ascii=False))
PY
```

3. If `--dry-run`, summarize what would change and prompt: "Run `/session-memory:migrate --apply` to commit changes."
4. If `--apply`, confirm completion and recommend `git status` to review.
