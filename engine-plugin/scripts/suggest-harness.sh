#!/bin/bash
# PostToolUse(Read) hook: suggest harness skills based on file content
# Loads patterns directly from matchPatterns in .claude/skills/harness-*.md frontmatter
# No external config file needed — falls back to description keywords if matchPatterns is absent
# Injects suggestions into Claude context via additionalContext JSON

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID_VAL=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR_VAL="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

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

  # Extract YAML frontmatter (between first --- and second ---)
  frontmatter=$(sed -n '2,/^---$/p' "$skill_file" | sed '$d')

  # Extract matchPatterns.fileGlob
  file_glob=$(echo "$frontmatter" | sed -n 's/^  fileGlob: *"\(.*\)"/\1/p' | head -1)

  # Filter by file path if fileGlob is present
  if [ -n "$file_glob" ]; then
    if ! echo "$FILE_PATH" | grep -qE "$file_glob"; then
      continue
    fi
  fi

  # Extract matchPatterns.regex array
  regexes=$(echo "$frontmatter" | sed -n '/^  regex:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')

  matched=false

  if [ -n "$regexes" ]; then
    # Match using matchPatterns.regex
    while IFS= read -r regex; do
      [ -n "$regex" ] || continue
      if echo "$CONTENT" | grep -qE "$regex"; then
        matched=true
        break
      fi
    done <<EOF_REGEX
$regexes
EOF_REGEX
  else
    # Fallback: extract keywords from description if matchPatterns is absent
    description=$(echo "$frontmatter" | sed -n 's/^description: *//p' | head -1)
    keywords=$(echo "$description" | sed 's/.*— //; s/\. .*//' | tr ',' '\n' | sed 's/^ *//; s/ *$//' | grep -v '^$')

    if [ -n "$keywords" ]; then
      while IFS= read -r kw; do
        [ -n "$kw" ] || continue
        if echo "$CONTENT" | grep -qi "$kw"; then
          matched=true
          break
        fi
      done <<EOF_KW
$keywords
EOF_KW
    fi
  fi

  if [ "$matched" = true ]; then
    # Extract label
    label=$(echo "$frontmatter" | sed -n 's/^description: *Use when working with \(.*\) —.*/\1/p' | head -1)
    [ -z "$label" ] && label="$skill_name"
    SUGGESTIONS="${SUGGESTIONS}$(printf '• /%s (%s detected)\n' "$skill_name" "$label")"
    SUGGESTIONS="${SUGGESTIONS}
"
  fi
done

# Remove trailing newline
SUGGESTIONS=$(echo "$SUGGESTIONS" | sed '/^$/d')

# Output suggestions as additionalContext if any were found
if [ -n "$SUGGESTIONS" ]; then
  MSG="Related harness skills detected. Please invoke the relevant skill before editing:\n${SUGGESTIONS}\n"
  ESCAPED_MSG=$(echo -e "$MSG" | jq -Rs .)
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
