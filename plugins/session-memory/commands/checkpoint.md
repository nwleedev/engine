---
description: Force a narration checkpoint for the current session
argument-hint: ""
---

# Force Checkpoint

Invoke the narration pipeline with `event="ManualCheckpoint"` so a CONTEXT file is written immediately regardless of time/size thresholds.

Run via Bash:

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-}"
TRANSCRIPT_PATH="${CLAUDE_TRANSCRIPT_PATH:-}"
CWD="$(pwd)"

if [ -z "$SESSION_ID" ] || [ -z "$TRANSCRIPT_PATH" ]; then
  echo "Missing CLAUDE_SESSION_ID or CLAUDE_TRANSCRIPT_PATH; cannot checkpoint."
  exit 1
fi

PAYLOAD=$(printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s"}' \
  "$SESSION_ID" "$TRANSCRIPT_PATH" "$CWD")

echo "$PAYLOAD" | python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "plugins/session-memory"), "scripts"))
import narration_pipeline
payload = json.load(sys.stdin)
narration_pipeline.run("ManualCheckpoint", payload)
PY

echo "Checkpoint requested."
```

After running, suggest: "Run `/session-memory:status` to see the result in the log."
