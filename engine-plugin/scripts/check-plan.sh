#!/bin/bash
# PreToolUse(Write|Edit) hook: block coding without a plan
# Exit 0 = allow, Exit 2 = block (stderr → forwarded to Claude)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Always allow files inside .claude/ (plan/session/skill edits)
if echo "$FILE_PATH" | grep -qE '\.claude/'; then
  exit 0
fi

# Always allow files inside temps/
if echo "$FILE_PATH" | grep -qE 'temps/'; then
  exit 0
fi

# Allow config files like lefthook.yml, package.json, etc.
if echo "$FILE_PATH" | grep -qE '(lefthook\.yml|\.eslintrc|eslint\.config|\.prettierrc|tsconfig)'; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
PLANS_DIR="${PROJECT_DIR}/.claude/plans"

# Check if plans directory exists
if [ ! -d "$PLANS_DIR" ]; then
  echo "No plan files found. Please create a plan in .claude/plans/ first." >&2
  exit 2
fi

# Check for plan files modified within the last 72 hours (259200 seconds)
NOW=$(date +%s)
FOUND_RECENT=false

for plan_file in "$PLANS_DIR"/*.md; do
  [ -f "$plan_file" ] || continue
  MTIME=$(stat -f %m "$plan_file" 2>/dev/null || stat -c %Y "$plan_file" 2>/dev/null)
  if [ -n "$MTIME" ]; then
    AGE=$(( NOW - MTIME ))
    if [ "$AGE" -lt 259200 ]; then
      FOUND_RECENT=true
      break
    fi
  fi
done

if [ "$FOUND_RECENT" = false ]; then
  echo "No plan files have been modified in the last 72 hours. Please create or update a plan first." >&2
  exit 2
fi

exit 0
