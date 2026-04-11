#!/bin/bash
# SessionEnd(clear) hook: backup SESSION.md → contexts/

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
SESSION_ID_VAL="${SESSION_ID:-$(echo "$INPUT" | jq -r '.session_id // empty')}"

[ -z "$SESSION_ID_VAL" ] && exit 0

SESSION_FILE="$PROJECT_DIR/.claude/sessions/$SESSION_ID_VAL/SESSION.md"
[ -f "$SESSION_FILE" ] || exit 0

CONTEXTS_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID_VAL/contexts"
mkdir -p "$CONTEXTS_DIR"
cp "$SESSION_FILE" "$CONTEXTS_DIR/CONTEXT-$(date +%Y%m%d-%H%M)-session-end.md"

exit 0
