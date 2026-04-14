#!/bin/bash
# Shared library: harness skill matching logic
# Source this file (do not execute directly) so that exported variables are visible to callers.
#
# Exposed functions:
#   harness_extract_frontmatter <skill_file>
#     Sets HARNESS_FRONTMATTER to the YAML block between the first and second --- delimiters.
#
#   harness_match_skill <skill_file> <tool_name> <content> <file_path>
#     Evaluates whether a harness skill matches the current context.
#     Sets:
#       HARNESS_MATCHED      — "true" or "false"
#       HARNESS_FRONTMATTER  — extracted frontmatter text
#       HARNESS_SKILL_LABEL  — label derived from the description field

# Extract YAML frontmatter from a skill file.
# Sets global HARNESS_FRONTMATTER.
harness_extract_frontmatter() {
  local skill_file="$1"
  HARNESS_FRONTMATTER=$(sed -n '2,/^---$/p' "$skill_file" | sed '$d')
}

# Evaluate whether a harness skill matches the given context.
# Parameters:
#   $1 skill_file  — full path to harness-*.md
#   $2 tool_name   — tool currently being invoked (reserved for future toolNames matching)
#   $3 content     — file content (first N lines) to match against regexes
#   $4 file_path   — file path being acted on, used for fileGlob matching
# Sets HARNESS_MATCHED, HARNESS_FRONTMATTER, HARNESS_SKILL_LABEL.
harness_match_skill() {
  local skill_file="$1"
  local _tool_name="$2"  # reserved for future toolNames / taskPrompt matching
  local content="$3"
  local file_path="$4"

  HARNESS_MATCHED=false
  HARNESS_FRONTMATTER=""
  HARNESS_SKILL_LABEL=""

  harness_extract_frontmatter "$skill_file"
  local frontmatter="$HARNESS_FRONTMATTER"

  # Extract matchPatterns.fileGlob
  local file_glob
  file_glob=$(printf '%s\n' "$frontmatter" | sed -n 's/^  fileGlob: *"\(.*\)"/\1/p' | head -1)

  # Filter by file path if fileGlob is present
  if [ -n "$file_glob" ]; then
    if ! printf '%s\n' "$file_path" | grep -qE "$file_glob"; then
      return
    fi
  fi

  # Extract matchPatterns.regex array
  local regexes
  regexes=$(printf '%s\n' "$frontmatter" | sed -n '/^  regex:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')

  local matched=false

  if [ -n "$regexes" ]; then
    # Match using matchPatterns.regex
    local regex
    while IFS= read -r regex; do
      [ -n "$regex" ] || continue
      if printf '%s\n' "$content" | grep -qE "$regex"; then
        matched=true
        break
      fi
    done <<EOF_REGEX
$regexes
EOF_REGEX
  else
    # Fallback: extract keywords from description if matchPatterns is absent
    local description
    description=$(printf '%s\n' "$frontmatter" | sed -n 's/^description: *//p' | head -1)
    local keywords
    keywords=$(printf '%s\n' "$description" | sed 's/.*— //; s/\. .*//' | tr ',' '\n' | sed 's/^ *//; s/ *$//' | grep -v '^$')

    if [ -n "$keywords" ]; then
      local kw
      while IFS= read -r kw; do
        [ -n "$kw" ] || continue
        if printf '%s\n' "$content" | grep -qi "$kw"; then
          matched=true
          break
        fi
      done <<EOF_KW
$keywords
EOF_KW
    fi
  fi

  HARNESS_MATCHED="$matched"

  if [ "$matched" = true ]; then
    # Extract label from description
    local label
    label=$(printf '%s\n' "$frontmatter" | sed -n 's/^description: *Use when working with \(.*\) —.*/\1/p' | head -1)
    local skill_name
    skill_name=$(basename "$skill_file" .md)
    [ -z "$label" ] && label="$skill_name"
    HARNESS_SKILL_LABEL="$label"
  fi
}
