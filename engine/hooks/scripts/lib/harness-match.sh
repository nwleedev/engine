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
#     Matching priority:
#       1. fileGlob  — filters by file path (must pass if set)
#       2. toolNames — glob patterns against tool_name; definitive match or reject
#       3. taskPrompt — regex patterns against content when tool_name == "Task"
#       4. regex     — content matching via matchPatterns.regex
#       5. keywords  — fallback from description field
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
#   $2 tool_name   — tool currently being invoked (e.g. Write, Edit, Task, mcp__*_figma__*)
#   $3 content     — file content (first N lines) or Task prompt to match against
#   $4 file_path   — file path being acted on, used for fileGlob matching
# Sets HARNESS_MATCHED, HARNESS_FRONTMATTER, HARNESS_SKILL_LABEL.
harness_match_skill() {
  local skill_file="$1"
  local tool_name="$2"
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

  # --- toolNames matching ---
  local toolnames
  toolnames=$(printf '%s\n' "$frontmatter" | sed -n '/^  toolNames:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')

  if [ -n "$toolnames" ]; then
    if [ -n "$tool_name" ]; then
      local tn_matched=false
      while IFS= read -r tn_pattern; do
        [ -n "$tn_pattern" ] || continue
        tn_pattern="${tn_pattern%"${tn_pattern##*[! ]}"}"
        case "$tool_name" in
          $tn_pattern) tn_matched=true; break;;
        esac
      done <<EOF_TN
$toolnames
EOF_TN
      if [ "$tn_matched" = true ]; then
        HARNESS_MATCHED=true
        local label
        label=$(printf '%s\n' "$frontmatter" | sed -n 's/^description: *Use when working with \(.*\) —.*/\1/p' | head -1)
        [ -z "$label" ] && label=$(basename "$skill_file" .md)
        HARNESS_SKILL_LABEL="$label"
        return
      else
        HARNESS_MATCHED=false
        return
      fi
    fi
  fi

  # --- taskPrompt matching (supplements regex; only when tool_name == "Task") ---
  local task_prompt_matched=false
  if [ "$tool_name" = "Task" ]; then
    local task_prompts
    task_prompts=$(printf '%s\n' "$frontmatter" | sed -n '/^  taskPrompt:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')
    if [ -n "$task_prompts" ]; then
      while IFS= read -r tp_regex; do
        [ -n "$tp_regex" ] || continue
        if printf '%s\n' "$content" | grep -qE "$tp_regex"; then
          task_prompt_matched=true
          break
        fi
      done <<EOF_TP
$task_prompts
EOF_TP
    fi
  fi

  # Extract matchPatterns.regex array
  local regexes
  regexes=$(printf '%s\n' "$frontmatter" | sed -n '/^  regex:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')

  local matched=false

  # taskPrompt match counts as an early positive result; skip regex if already matched
  if [ "$task_prompt_matched" = true ]; then
    matched=true
  fi

  if [ "$matched" = false ] && [ -n "$regexes" ]; then
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
  elif [ "$matched" = false ]; then
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
