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

found_harness=false
for _f in "$SKILLS_DIR"/harness-*.md; do
  [ -f "$_f" ] && { found_harness=true; break; }
done
[ "$found_harness" = true ] || exit 0

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

# --- Cache check ---

SKILLS_MTIME=$(stat -f %m "$SKILLS_DIR" 2>/dev/null || stat -c %Y "$SKILLS_DIR" 2>/dev/null)

LOG_DIR=""
if [ -n "$SESSION_ID" ]; then
  LOG_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
  mkdir -p "$LOG_DIR"
fi

FILE_PATH_EARLY=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CACHE_KEY="$TOOL_NAME:$FILE_PATH_EARLY"

if [ -n "$LOG_DIR" ] && [ -f "$LOG_DIR/.harness-cache" ]; then
  CACHED_MTIME=$(grep '^SKILLS_MTIME=' "$LOG_DIR/.harness-cache" | cut -d= -f2 | head -1)
  if [ "$CACHED_MTIME" = "$SKILLS_MTIME" ]; then
    # Skills unchanged — check if already injected for this context
    if grep -qF "INJECTED=$CACHE_KEY:" "$LOG_DIR/.harness-cache" 2>/dev/null; then
      exit 0  # Already injected for this tool/file combo
    fi
  else
    # Skills changed — invalidate cache
    printf 'SKILLS_MTIME=%s\n' "$SKILLS_MTIME" > "$LOG_DIR/.harness-cache"
  fi
elif [ -n "$LOG_DIR" ]; then
  # Initialize cache file
  printf 'SKILLS_MTIME=%s\n' "$SKILLS_MTIME" > "$LOG_DIR/.harness-cache"
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

HIGHEST_ENFORCEMENT=0
HIGHEST_ENFORCEMENT_SKILL=""
HIGHEST_ENFORCEMENT_REASON=""
HIGHEST_ENFORCEMENT_BYPASS=""

for skill_file in "$SKILLS_DIR"/harness-*.md; do
  [ -f "$skill_file" ] || continue
  skill_name=$(basename "$skill_file" .md)

  harness_match_skill "$skill_file" "$TOOL_NAME" "$MATCH_CONTENT" "$MATCH_FILE_PATH"

  if [ "$HARNESS_MATCHED" = "true" ]; then
    enforcement=$(printf '%s\n' "$HARNESS_FRONTMATTER" | sed -n 's/^enforcement: *//p' | head -1 | tr -d '"' | tr -d "'")
    enforcement_reason=$(printf '%s\n' "$HARNESS_FRONTMATTER" | sed -n 's/^enforcementReason: *//p' | head -1 | sed 's/^"//; s/"$//')
    enforcement_bypass=$(printf '%s\n' "$HARNESS_FRONTMATTER" | sed -n 's/^enforcementBypass: *//p' | head -1 | sed 's/^"//; s/"$//')
    [ -z "$enforcement" ] && enforcement="advisory"

    enf_level=0
    case "$enforcement" in
      ask) enf_level=1 ;;
      inject) enf_level=2 ;;
    esac
    if [ "$enf_level" -gt "$HIGHEST_ENFORCEMENT" ]; then
      HIGHEST_ENFORCEMENT=$enf_level
      HIGHEST_ENFORCEMENT_SKILL="$skill_name"
      HIGHEST_ENFORCEMENT_REASON="$enforcement_reason"
      HIGHEST_ENFORCEMENT_BYPASS="$enforcement_bypass"
    fi

    if [ -n "$LOG_DIR" ]; then
      case "$enforcement" in
        ask)    printf '[ASK] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage" ;;
        inject) printf '[INJECT] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage" ;;
        *)      printf '[MATCH] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage" ;;
      esac
    fi

    MATCHED_SKILLS+=("$skill_name")
    excerpt=$(head -n 50 "$skill_file")
    MATCHED_EXCERPTS+=("$excerpt")
  else
    if [ -n "$LOG_DIR" ]; then
      printf '[NOMATCH] %s %s\n' "$TOOL_NAME" "$skill_name" >> "$LOG_DIR/.harness-usage"
    fi
  fi
done

# --- Compose context_text (used by inject and advisory paths) ---

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

# --- Enforcement handling ---

if [ "$HIGHEST_ENFORCEMENT" -ge 2 ]; then
  # inject: prepend harness content into prompt for Task; downgrade to ask for Write/Edit; additionalContext for mcp__*
  case "$TOOL_NAME" in
    Task)
      injected_prompt="=== HARNESS INJECTION: $HIGHEST_ENFORCEMENT_SKILL ===
[Harness rules active — follow strictly]
${context_text}
=== END HARNESS ===

${TASK_PROMPT}"
      updated_input=$(printf '%s' "$INPUT" | jq --arg p "$injected_prompt" '.tool_input + {prompt: $p}')
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","updatedInput":%s}}\n' "$updated_input"
      exit 0
      ;;
    Write|Edit)
      # Modifying file content is risky; downgrade inject to ask for these tools
      reason="Harness enforcement active (inject downgraded to ask for file edits) — $HIGHEST_ENFORCEMENT_SKILL"
      [ -n "$HIGHEST_ENFORCEMENT_REASON" ] && reason="$reason: $HIGHEST_ENFORCEMENT_REASON"
      [ -n "$HIGHEST_ENFORCEMENT_BYPASS" ] && reason="$reason. To bypass: $HIGHEST_ENFORCEMENT_BYPASS"
      reason_json=$(printf '%s' "$reason" | jq -Rs .)
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":%s}}\n' "$reason_json"
      exit 0
      ;;
    *)
      # mcp__* and others: fall through to additionalContext output
      ;;
  esac
elif [ "$HIGHEST_ENFORCEMENT" -ge 1 ]; then
  # ask: output permissionDecision
  reason="Harness enforcement active — $HIGHEST_ENFORCEMENT_SKILL"
  [ -n "$HIGHEST_ENFORCEMENT_REASON" ] && reason="$reason: $HIGHEST_ENFORCEMENT_REASON"
  [ -n "$HIGHEST_ENFORCEMENT_BYPASS" ] && reason="$reason. To bypass: $HIGHEST_ENFORCEMENT_BYPASS"
  reason_json=$(printf '%s' "$reason" | jq -Rs .)
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":%s}}\n' "$reason_json"
  exit 0
fi

# --- Advisory: output additionalContext ---

# Output JSON with additionalContext
additional_context_json=$(printf '%s' "$context_text" | jq -Rs .) || exit 0

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":%s}}\n' "$additional_context_json"

# Record injections in cache
if [ -n "$LOG_DIR" ] && [ -f "$LOG_DIR/.harness-cache" ]; then
  for injected_skill in "${MATCHED_SKILLS[@]}"; do
    printf 'INJECTED=%s:%s\n' "$CACHE_KEY" "$injected_skill" >> "$LOG_DIR/.harness-cache"
  done
fi

exit 0
