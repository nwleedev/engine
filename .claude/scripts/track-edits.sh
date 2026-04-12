#!/bin/bash
# PostToolUse(Write|Edit) hook: track edited files + suggest work-reviewer
# Injects suggestions into Claude context via additionalContext JSON

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

# Skip tracking if SESSION_ID is missing
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
EDITED_FILES="$SESSION_DIR/.edited-files"

# Ensure session directory exists
mkdir -p "$SESSION_DIR"

# Append file path (deduplicated) — records all edits (shared by snapshot + reviewer)
if [ -n "$FILE_PATH" ]; then
  if ! grep -qxF "$FILE_PATH" "$EDITED_FILES" 2>/dev/null; then
    echo "$FILE_PATH" >> "$EDITED_FILES"
  fi
fi

# work-reviewer count: exclude all auto-generated paths (sessions/, meta/, feeds/)
REVIEW_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  REVIEW_COUNT=$(grep -cvE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null || echo "0")
fi

# Extract edited file list (excluding sessions/meta/feeds)
EDITED_LIST=""
if [ -f "$EDITED_FILES" ]; then
  EDITED_LIST=$(grep -vE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null | head -20 | tr '\n' ', ' | sed 's/,$//')
fi

# Load engine config
ENGINE_CONFIG="$PROJECT_DIR/.claude/engine.env"
if [ -f "$ENGINE_CONFIG" ]; then
  # shellcheck source=/dev/null
  . "$ENGINE_CONFIG"
fi
REVIEW_THRESHOLD_SINGLE="${REVIEW_THRESHOLD_SINGLE:-2}"
REVIEW_THRESHOLD_MULTI="${REVIEW_THRESHOLD_MULTI:-5}"

# Detect infrastructure files: .json, .yaml, .yml, .sh, .toml, Dockerfile, settings, etc.
INFRA_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  INFRA_COUNT=$(grep -vE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null \
    | grep -cE '\.(json|yaml|yml|sh|toml)$|Dockerfile|settings\.' 2>/dev/null || echo "0")
fi

# Build perspective-based review message
build_review_msg() {
  local count="$1" list="$2" multi="$3"
  if [ "$multi" = true ] && [ -n "${REVIEW_AGENTS:-}" ]; then
    # When REVIEW_AGENTS is set: parallel review by perspective
    local agent_lines=""
    IFS=',' read -r -a PERSPECTIVES <<< "$REVIEW_AGENTS"
    for P in "${PERSPECTIVES[@]}"; do
      P=$(echo "$P" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      agent_lines="${agent_lines}\\n- work-reviewer (perspective: ${P})"
    done
    echo "${count} file(s) modified (${list}). Run the following perspective-based parallel reviews:${agent_lines}"
  elif [ "$multi" = true ]; then
    echo "${count} file(s) modified (${list}). Infrastructure/large-scale change detected: run multi-review (2 parallel reviewers) before completion."
  else
    echo "${count} file(s) modified (${list}). Run the work-reviewer agent before completion."
  fi
}

# Tiered review suggestions
if [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_MULTI" ] || { [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_SINGLE" ] && [ "$INFRA_COUNT" -ge 1 ]; }; then
  MSG=$(build_review_msg "$REVIEW_COUNT" "$EDITED_LIST" true)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$MSG"
  }
}
EOF
elif [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_SINGLE" ]; then
  MSG=$(build_review_msg "$REVIEW_COUNT" "$EDITED_LIST" false)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$MSG"
  }
}
EOF
fi

exit 0
