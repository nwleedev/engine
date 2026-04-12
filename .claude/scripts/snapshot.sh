#!/bin/bash
# Stop/PreCompact hook: automatic session snapshot creation
# 3 tiers: pre-compact (always), auto (when edits exist), mini (read-only turns)

INPUT=$(cat)

# Prevent infinite loop: exit immediately if Stop hook is already active
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

# Exit if SESSION_ID is not set
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"

# Create session directory if it doesn't exist
if [ ! -d "$SESSION_DIR" ]; then
  mkdir -p "$SESSION_DIR/contexts" "$SESSION_DIR/notes"
fi

EDITED_FILES="$SESSION_DIR/.edited-files"
READ_FILES="$SESSION_DIR/.read-files"

HAS_EDITS=false
if [ -f "$EDITED_FILES" ] && [ -s "$EDITED_FILES" ]; then
  HAS_EDITS=true
fi

HAS_READS=false
if [ -f "$READ_FILES" ] && [ -s "$READ_FILES" ]; then
  HAS_READS=true
fi

# Skip if no edits and no reads (simple Q&A turn)
# Always create snapshot for --pre-compact
if [ "$1" != "--pre-compact" ] && [ "$HAS_EDITS" = false ] && [ "$HAS_READS" = false ]; then
  exit 0
fi

# Collect snapshot data
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
DATE_FILE=$(date +"%Y%m%d-%H%M")
# === Structured transcript extraction ===
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

USER_REQUEST=""
KEY_ACTIONS=""
COMMITS=""
ERRORS=""

if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # Cache recent messages (read once, created in session directory)
  RECENT_CACHE=$(mktemp "$SESSION_DIR/.cache-XXXXXX")
  tail -500 "$TRANSCRIPT_PATH" > "$RECENT_CACHE"

  # 1. User request: last human message text (what triggered this turn)
  USER_REQUEST=$(jq -r '
    select(.type == "human") | .message.content[]? |
    select(.type == "text") | .text
  ' "$RECENT_CACHE" 2>/dev/null | tail -1 | tr '\n' ' ' | head -c 300)

  # 2. Key actions: only significant actions (skip file Read/Edit/Write/Grep/Glob)
  KEY_ACTIONS=$(jq -r '
    select(.type == "assistant") | .message.content[]? |
    select(.type == "tool_use") |
    if .name == "Agent" then
      "- Agent(\(.input.subagent_type // "general")): \(.input.description // "")"
    elif .name == "Skill" then
      "- Skill: \(.input.skill // "")"
    elif .name == "EnterPlanMode" or .name == "ExitPlanMode" then
      "- \(.name)"
    elif .name == "Bash" then
      (.input.command // "") as $cmd |
      if ($cmd | test("^(npm |npx |pnpm |yarn |bun |make |docker |pytest |cargo |go test|git push|git checkout|git merge|git rebase)")) then
        "- Bash: \($cmd | .[0:80])"
      else empty end
    else empty end
  ' "$RECENT_CACHE" 2>/dev/null | head -15)

  # 3. Commits: extract from tool_result output (session-isolated, not git log)
  # git commit output format: "[branch hash] commit subject"
  COMMITS=$(jq -r '
    select(.type == "user") | .message.content[]? |
    select(.type == "tool_result") |
    (if .content | type == "string" then .content
     else (.content[]? | select(.type == "text") | .text) end) // empty
  ' "$RECENT_CACHE" 2>/dev/null | grep -E '^\[[a-zA-Z0-9/_.-]+ [a-f0-9]{7,}\] ' | sed 's/^\[[^ ]* [a-f0-9]*\] /- /' | head -5)

  # 4. Errors: count tool_result errors
  ERROR_COUNT=$(jq -s '[.[] | select(.type == "user") | .message.content[]? | select(.type == "tool_result" and .is_error == true)] | length' "$RECENT_CACHE" 2>/dev/null)
  if [ "${ERROR_COUNT:-0}" -gt 0 ] 2>/dev/null; then
    ERRORS="${ERROR_COUNT} tool error(s)"
  fi

  rm -f "$RECENT_CACHE"
fi

# Edited files list (relative paths)
FILES_LIST=""
if [ -f "$EDITED_FILES" ]; then
  FILES_LIST=$(sort -u "$EDITED_FILES" | sed "s|^$PROJECT_DIR/||" | head -20)
fi

# Plan path (relative) — prefer session pointer for parallel-terminal isolation
PLAN_FILE=""
if [ -f "$SESSION_DIR/.current-plan" ]; then
  PTR=$(cat "$SESSION_DIR/.current-plan" 2>/dev/null)
  if [ -n "$PTR" ] && [ -f "$PTR" ]; then
    PLAN_FILE=$(echo "$PTR" | sed "s|^$PROJECT_DIR/||")
  fi
fi
if [ -z "$PLAN_FILE" ] && [ -d "$PROJECT_DIR/.claude/plans" ]; then
  PLAN_FILE=$(ls -t "$PROJECT_DIR/.claude/plans/"*.md 2>/dev/null | head -1 | sed "s|^$PROJECT_DIR/||")
fi

# Determine snapshot type
IS_MINI=false
if [ "$1" = "--pre-compact" ]; then
  TITLE="pre-compact"
elif [ "$HAS_EDITS" = true ]; then
  TITLE="auto"
else
  TITLE="mini"
  IS_MINI=true
fi
SNAP_FILE="$SESSION_DIR/contexts/CONTEXT-${DATE_FILE}-${TITLE}.md"

# Ensure contexts/ directory exists
mkdir -p "$SESSION_DIR/contexts"

# Count files (deduplicated, consistent with FILES_LIST)
FILE_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  FILE_COUNT=$(sort -u "$EDITED_FILES" | wc -l | tr -d ' ')
fi

# Generate deterministic summary line
SUMMARY_LINE=""
[ "$FILE_COUNT" -gt 0 ] && SUMMARY_LINE="Edited ${FILE_COUNT} file(s)"
if [ -n "$COMMITS" ]; then
  COMMIT_COUNT=$(echo "$COMMITS" | grep -c '^-')
  FIRST_COMMIT=$(echo "$COMMITS" | head -1 | sed 's/^- //' | head -c 60)
  SUMMARY_LINE="${SUMMARY_LINE:+$SUMMARY_LINE. }${COMMIT_COUNT} commit(s): \"${FIRST_COMMIT}\""
fi
[ -n "$ERRORS" ] && SUMMARY_LINE="${SUMMARY_LINE:+$SUMMARY_LINE. }$ERRORS"
[ -z "$SUMMARY_LINE" ] && SUMMARY_LINE="(no file changes)"

# Notes: only include .turn-summary if it has structured ## Outcome heading
NOTES=""
TURN_SUMMARY_FILE="$SESSION_DIR/.turn-summary"
if [ -f "$TURN_SUMMARY_FILE" ] && [ -s "$TURN_SUMMARY_FILE" ]; then
  if grep -q '^## Outcome' "$TURN_SUMMARY_FILE"; then
    NOTES=$(head -c 2000 "$TURN_SUMMARY_FILE")
  fi
  > "$TURN_SUMMARY_FILE"
fi

# Generate snapshot file
{
  echo "# Snapshot: $TITLE"
  echo "Date: $TIMESTAMP"
  echo ""
  echo "## Request"
  if [ -n "$USER_REQUEST" ]; then
    echo "> $USER_REQUEST"
  else
    echo "(no request captured)"
  fi
  echo ""
  echo "## Summary"
  echo "$SUMMARY_LINE"
  if [ -n "$KEY_ACTIONS" ]; then
    echo ""
    echo "## Key actions"
    echo "$KEY_ACTIONS"
  fi
  echo ""
  echo "## Files changed"
  if [ -n "$FILES_LIST" ]; then
    echo "$FILES_LIST" | sed 's/^/- /'
  else
    echo "(none)"
  fi
  echo ""
  echo "## Commits"
  echo "${COMMITS:-(none)}"
  echo ""
  echo "## Errors"
  echo "${ERRORS:-(none)}"
  echo ""
  echo "## Active plan"
  echo "${PLAN_FILE:-(none)}"
  if [ -n "$NOTES" ]; then
    echo ""
    echo "## Notes"
    echo "$NOTES"
  fi
} > "$SNAP_FILE"

# Create or update SESSION.md
SESSION_MD="$SESSION_DIR/SESSION.md"

# Mini-snapshots are saved only to contexts/, skip SESSION.md (preserve 80-line limit)
if [ "$IS_MINI" = true ]; then
  [ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
  [ -f "$READ_FILES" ] && > "$READ_FILES"
  exit 0
fi

# full/pre-compact: update SESSION.md
REQUEST_LINE=$(echo "$USER_REQUEST" | tr '\n' ' ' | head -c 100)
[ -z "$REQUEST_LINE" ] && REQUEST_LINE="(no request captured)"
DONE_LINE=$(echo "$SUMMARY_LINE" | head -c 120)

SUMMARY="### $TIMESTAMP — $TITLE
- Request: $REQUEST_LINE
- Done: $DONE_LINE
- Files ($FILE_COUNT): $(echo "$FILES_LIST" | tr '\n' ', ' | sed 's/,$//')"

if [ ! -f "$SESSION_MD" ]; then
  cat > "$SESSION_MD" << SESSIONEOF
# Session Log

## Goal
(Session goal not set)

## Active Decisions

## Snapshots (newest first)

$SUMMARY
SESSIONEOF
else
  TEMP_FILE=$(mktemp "$SESSION_DIR/.session-md-XXXXXX")
  {
    sed -n '1,/^## Snapshots/p' "$SESSION_MD"
    echo ""
    echo "$SUMMARY"
    echo ""
    sed -n '/^## Snapshots/,$ { /^## Snapshots/d; p; }' "$SESSION_MD"
  } > "$TEMP_FILE"

  head -80 "$TEMP_FILE" > "$SESSION_MD"
  rm -f "$TEMP_FILE"
fi

# Reset file lists
[ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
[ -f "$READ_FILES" ] && > "$READ_FILES"

exit 0
