#!/bin/bash
# PostToolUse(Read) hook: suggest harness skills based on file content
# Loads patterns directly from matchPatterns in .claude/skills/harness-*.md frontmatter
# No external config file needed — falls back to description keywords if matchPatterns is absent
# Injects suggestions into Claude context via additionalContext JSON

# shellcheck source=lib/harness-match.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib/harness-match.sh"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID_VAL=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR_VAL="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

# Load engine config so HARNESS_LEGACY_SUGGEST can be set in .claude/engine.env
ENGINE_CONFIG="$PROJECT_DIR_VAL/.claude/engine.env"
if [ -f "$ENGINE_CONFIG" ]; then
  # shellcheck source=/dev/null
  . "$ENGINE_CONFIG"
fi

# Only run when HARNESS_LEGACY_SUGGEST=1 (inject-harness.sh is the default path)
[ "${HARNESS_LEGACY_SUGGEST:-0}" = "1" ] || exit 0

# Track read files — used by snapshot.sh for mini-snapshot decisions
if [ -n "$SESSION_ID_VAL" ] && [ -n "$PROJECT_DIR_VAL" ] && [ -n "$FILE_PATH" ]; then
  READ_FILE="$PROJECT_DIR_VAL/.claude/sessions/$SESSION_ID_VAL/.read-files"
  mkdir -p "$(dirname "$READ_FILE")"
  if ! grep -qxF "$FILE_PATH" "$READ_FILE" 2>/dev/null; then
    echo "$FILE_PATH" >> "$READ_FILE"
  fi
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Check if harness skills directory exists
SKILLS_DIR="$PROJECT_DIR_VAL/.claude/skills"
if [ ! -d "$SKILLS_DIR" ]; then
  exit 0
fi

CONTENT=$(head -100 "$FILE_PATH" 2>/dev/null)
SUGGESTIONS=""

# Iterate over each harness skill
for skill_file in "$SKILLS_DIR"/harness-*.md; do
  [ -f "$skill_file" ] || continue

  skill_name=$(basename "$skill_file" .md)

  harness_match_skill "$skill_file" "" "$CONTENT" "$FILE_PATH"

  if [ "$HARNESS_MATCHED" = true ]; then
    SUGGESTIONS="${SUGGESTIONS}$(printf '• /%s (%s detected)\n' "$skill_name" "$HARNESS_SKILL_LABEL")"
    SUGGESTIONS="${SUGGESTIONS}
"
  fi
done

# Remove trailing newline
SUGGESTIONS=$(echo "$SUGGESTIONS" | sed '/^$/d')

# Output suggestions as additionalContext if any were found
if [ -n "$SUGGESTIONS" ]; then
  MSG="Related harness skills detected. Please invoke the relevant skill before editing:\n${SUGGESTIONS}\n"
  ESCAPED_MSG=$(printf '%b' "$MSG" | jq -Rs .)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": ${ESCAPED_MSG}
  }
}
EOF
fi

exit 0
