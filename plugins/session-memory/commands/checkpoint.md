---
description: Force a narration checkpoint for the current session
argument-hint: ""
---

# Force Checkpoint

Invoke the narration pipeline with `event="ManualCheckpoint"` so a CONTEXT file is written immediately regardless of time/size thresholds.

Run via Bash:

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-}"
CWD="$(pwd)"

# Encode cwd: replace / with -
ENCODED_CWD=$(echo "$CWD" | sed 's|/|-|g')
PROJECT_DIR="$HOME/.claude/projects/$ENCODED_CWD"

# Resolve session id and transcript path
if [ -n "$SESSION_ID" ]; then
  TRANSCRIPT_PATH="$PROJECT_DIR/$SESSION_ID.jsonl"
else
  # Latest .jsonl in project dir
  TRANSCRIPT_PATH=$(ls -1t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
  SESSION_ID=$(basename "${TRANSCRIPT_PATH%.jsonl}")
fi

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  echo "checkpoint: cannot resolve transcript path. CWD=$CWD ENCODED=$ENCODED_CWD"
  exit 1
fi

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PAYLOAD=$(printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s"}' \
  "$SESSION_ID" "$TRANSCRIPT_PATH" "$PROJECT_ROOT")

echo "$PAYLOAD" | python3 - <<'PY'
import json, os, sys
project_root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
# Try plugin location
for candidate in [
    os.path.join(project_root, "plugins", "session-memory", "scripts"),
    os.path.expanduser("~/.claude/plugins/session-memory/scripts"),
]:
    if os.path.isdir(candidate):
        sys.path.insert(0, candidate)
        break
import narration_pipeline
payload = json.load(sys.stdin)
narration_pipeline.run("ManualCheckpoint", payload)
PY

echo "Checkpoint requested for session ${SESSION_ID:0:8}…. Run /session-memory:status to see the result."
```

After running, suggest: "Run `/session-memory:status` to see the result in the log."
