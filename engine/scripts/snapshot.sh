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
TOOL_CALLS=$(echo "$INPUT" | jq -r '.tool_calls_made // 0')

# === Structured transcript extraction ===
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

TOOLS_USED=""
COMMITS=""
ERRORS=""
TURN_SUMMARY=""

if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # Cache recent messages (read once, created in session directory)
  RECENT_CACHE=$(mktemp "$SESSION_DIR/.cache-XXXXXX")
  tail -500 "$TRANSCRIPT_PATH" > "$RECENT_CACHE"

  # 1. Tools used: extract tool names + targets from tool_use blocks (exclude Read/Grep/Glob — already in Files read)
  TOOLS_USED=$(jq -r '
    select(.type == "assistant") | .message.content[]? |
    select(.type == "tool_use") |
    if .name == "Write" or .name == "Edit" then
      "- \(.name) \(.input.file_path // "")"
    elif .name == "Bash" then
      "- Bash: \(.input.command // "" | .[0:80])"
    elif .name == "Agent" then
      "- Agent(\(.input.subagent_type // "general")): \(.input.description // "")"
    elif .name == "Skill" then
      "- Skill: \(.input.skill // "")"
    elif .name == "Read" or .name == "Grep" or .name == "Glob" or .name == "ToolSearch" then
      empty
    else
      "- \(.name)"
    end
  ' "$RECENT_CACHE" 2>/dev/null | head -30)

  # 2. Commits: extract git commit commands
  COMMITS=$(jq -r '
    select(.type == "assistant") | .message.content[]? |
    select(.type == "tool_use" and .name == "Bash") |
    .input.command // "" | select(test("git commit")) | .[0:120]
  ' "$RECENT_CACHE" 2>/dev/null | sed 's/^/- /' | head -5)

  # 3. Errors: count tool_result errors (JSONL requires --slurp)
  ERROR_COUNT=$(jq -s '[.[] | select(.type == "user") | .message.content[]? | select(.type == "tool_result" and .is_error == true)] | length' "$RECENT_CACHE" 2>/dev/null)
  if [ "${ERROR_COUNT:-0}" -gt 0 ] 2>/dev/null; then
    ERRORS="${ERROR_COUNT} tool error(s)"
  fi

  # 4. Turn summary: prefer .turn-summary (written by agent hook or main session), fallback to minimal extraction
  TURN_SUMMARY_FILE="$SESSION_DIR/.turn-summary"
  if [ -f "$TURN_SUMMARY_FILE" ] && [ -s "$TURN_SUMMARY_FILE" ]; then
    TURN_SUMMARY=$(head -c 4000 "$TURN_SUMMARY_FILE")
    > "$TURN_SUMMARY_FILE"
  else
    # Minimal fallback: last 5 lines of assistant text (in case agent hook failed)
    TURN_SUMMARY=$(jq -r '
      select(.type == "assistant") | .message.content[]? |
      select(.type == "text") | .text
    ' "$RECENT_CACHE" 2>/dev/null | tail -5 | head -c 1000)
  fi

  rm -f "$RECENT_CACHE"
fi

# Fallback if transcript parsing failed
if [ -z "$TURN_SUMMARY" ]; then
  TURN_SUMMARY=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' | head -c 4000)
fi

# Edited files list
FILES_LIST=""
if [ -f "$EDITED_FILES" ]; then
  FILES_LIST=$(sort -u "$EDITED_FILES" | head -20)
fi

# Read files list
READS_LIST=""
if [ -f "$READ_FILES" ]; then
  READS_LIST=$(sort -u "$READ_FILES" | head -20)
fi

# Plan path
PLAN_FILE=""
if [ -d "$PROJECT_DIR/.claude/plans" ]; then
  PLAN_FILE=$(ls -t "$PROJECT_DIR/.claude/plans/"*.md 2>/dev/null | head -1)
fi

# Determine snapshot type
IS_MINI=false
if [ "$1" = "--pre-compact" ]; then
  TITLE="pre-compact"
elif [ "$HAS_EDITS" = true ]; then
  TITLE="auto"
else
  # Read-only turn with no edits → mini-snapshot
  TITLE="mini"
  IS_MINI=true
fi
SNAP_FILE="$SESSION_DIR/contexts/CONTEXT-${DATE_FILE}-${TITLE}.md"

# Ensure contexts/ directory exists
mkdir -p "$SESSION_DIR/contexts"

# Count files
FILE_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  FILE_COUNT=$(wc -l < "$EDITED_FILES" | tr -d ' ')
fi
READ_COUNT=0
if [ -f "$READ_FILES" ]; then
  READ_COUNT=$(wc -l < "$READ_FILES" | tr -d ' ')
fi

# Generate snapshot file
cat > "$SNAP_FILE" << SNAPEOF
# Snapshot: $TITLE
Date: $TIMESTAMP
Tool calls: $TOOL_CALLS | Files edited: $FILE_COUNT | Files read: $READ_COUNT

## Files changed
$FILES_LIST

## Files read
$READS_LIST

## Tools used
${TOOLS_USED:-(none)}

## Commits
${COMMITS:-(none)}

## Errors
${ERRORS:-(none)}

## Active plan
$PLAN_FILE

## Turn summary
$TURN_SUMMARY
SNAPEOF

# Create or update SESSION.md
SESSION_MD="$SESSION_DIR/SESSION.md"

# Mini-snapshots are saved only to contexts/, skip SESSION.md (preserve 80-line limit)
if [ "$IS_MINI" = true ]; then
  # Reset file lists (maintain symmetry)
  [ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
  [ -f "$READ_FILES" ] && > "$READ_FILES"
  exit 0
fi

# full/pre-compact: update SESSION.md
DONE_LINE=$(echo "$TURN_SUMMARY" | grep -v '^$' | grep -v '^#' | head -1 | head -c 120)
[ -z "$DONE_LINE" ] && DONE_LINE="(auto-snapshot)"

SUMMARY="### $TIMESTAMP — $TITLE
- Done: $DONE_LINE
- Files ($FILE_COUNT): $(echo "$FILES_LIST" | tr '\n' ', ' | sed 's/,$//')
- Tool calls: $TOOL_CALLS"

if [ ! -f "$SESSION_MD" ]; then
  # Create initial SESSION.md
  cat > "$SESSION_MD" << SESSIONEOF
# Session Log

## Goal
(Session goal not set)

## Active Decisions

## Snapshots (newest first)

$SUMMARY
SESSIONEOF
else
  # Prepend snapshot to existing SESSION.md
  TEMP_FILE=$(mktemp "$SESSION_DIR/.session-md-XXXXXX")
  {
    # Preserve Goal and Active Decisions sections
    sed -n '1,/^## Snapshots/p' "$SESSION_MD"
    echo ""
    echo "$SUMMARY"
    echo ""
    # Preserve existing snapshots
    sed -n '/^## Snapshots/,$ { /^## Snapshots/d; p; }' "$SESSION_MD"
  } > "$TEMP_FILE"

  # Enforce 80-line limit
  head -80 "$TEMP_FILE" > "$SESSION_MD"
  rm -f "$TEMP_FILE"
fi

# Reset file lists
[ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
[ -f "$READ_FILES" ] && > "$READ_FILES"

exit 0
