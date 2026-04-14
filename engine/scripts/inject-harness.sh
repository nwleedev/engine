#!/bin/bash
# PreToolUse hook: inject matching harness skill content into Claude's context
# Fires before Write, Edit, Task, and mcp__* tool calls.
# Matches harness-*.md skills from .claude/skills/ and injects excerpts as additionalContext.

# shellcheck source=lib/harness-match.sh

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
CLAUDE_VERSION=$(echo "$INPUT" | jq -r '.claude_version // empty')

# --- Early exits ---

[ -n "$PROJECT_DIR" ] || exit 0

SKILLS_DIR="$PROJECT_DIR/.claude/skills"
[ -d "$SKILLS_DIR" ] || exit 0

harness_count=$(ls "$SKILLS_DIR"/harness-*.md 2>/dev/null | wc -l)
[ "$harness_count" -gt 0 ] || exit 0

# --- Version check ---

version_lt() {
  # Returns true if $1 < $2 (semantic versioning, major.minor.patch)
  [ "$(printf '%s\n' "$1" "$2" | sort -t. -k1,1n -k2,2n -k3,3n | head -1)" = "$1" ] && [ "$1" != "$2" ]
}

if [ -n "$CLAUDE_VERSION" ]; then
  if version_lt "$CLAUDE_VERSION" "2.1.9"; then
    printf 'inject-harness: warning: Claude version %s is below 2.1.9; harness injection may not be supported\n' "$CLAUDE_VERSION" >&2
    exit 0
  fi
fi

# --- Source matching library ---

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/lib/harness-match.sh" ] || { printf 'inject-harness: error: lib/harness-match.sh not found at %s\n' "$SCRIPT_DIR" >&2; exit 0; }
source "$SCRIPT_DIR/lib/harness-match.sh"

# --- Extract match content ---

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TASK_PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty')

if [ "$TOOL_NAME" = "Task" ]; then
  MATCH_CONTENT="$TASK_PROMPT"
  MATCH_FILE_PATH=""
else
  if [ -f "$FILE_PATH" ]; then
    MATCH_CONTENT=$(head -100 "$FILE_PATH" 2>/dev/null)
  else
    MATCH_CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.content // empty' | head -c 2000)
  fi
  MATCH_FILE_PATH="$FILE_PATH"
fi

# --- Match each harness skill ---

MATCHED_SKILLS=()
MATCHED_EXCERPTS=()

LOG_DIR=""
if [ -n "$SESSION_ID" ]; then
  LOG_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
  mkdir -p "$LOG_DIR"
fi

for skill_file in "$SKILLS_DIR"/harness-*.md; do
  [ -f "$skill_file" ] || continue
  skill_name=$(basename "$skill_file" .md)

  harness_match_skill "$skill_file" "$TOOL_NAME" "$MATCH_CONTENT" "$MATCH_FILE_PATH"

  if [ -n "$LOG_DIR" ]; then
    if [ "$HARNESS_MATCHED" = "true" ]; then
      printf '[MATCH] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage"
    else
      printf '[NOMATCH] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage"
    fi
  fi

  if [ "$HARNESS_MATCHED" = "true" ]; then
    MATCHED_SKILLS+=("$skill_name")
    excerpt=$(head -n 50 "$skill_file")
    MATCHED_EXCERPTS+=("$excerpt")
  fi
done

# --- Compose and output additionalContext ---

[ "${#MATCHED_SKILLS[@]}" -gt 0 ] || exit 0

context_text="=== Harness Skills Active ===
The following harness rules apply to this operation. Follow them carefully.
"

i=0
while [ "$i" -lt "${#MATCHED_SKILLS[@]}" ]; do
  skill_name="${MATCHED_SKILLS[$i]}"
  excerpt="${MATCHED_EXCERPTS[$i]}"
  context_text="$context_text
--- [$skill_name] ---
$excerpt
"
  i=$((i + 1))
done

# Limit to 10,000 characters
MAX_LEN=10000
if [ "${#context_text}" -gt "$MAX_LEN" ]; then
  context_text="${context_text:0:$MAX_LEN}"
  # Find the last matched skill for the truncation note
  last_skill="${MATCHED_SKILLS[${#MATCHED_SKILLS[@]}-1]}"
  context_text="$context_text
[... truncated, see full file at .claude/skills/$last_skill.md]"
fi

# Output JSON with additionalContext
additional_context_json=$(printf '%s' "$context_text" | jq -Rs .) || exit 0

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":%s}}\n' "$additional_context_json"

exit 0
