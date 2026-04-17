#!/bin/bash
# PreToolUse(Task) hook: enforce RESEARCH_PERSPECTIVES on project-researcher dispatch
# Blocks single-perspective calls by checking whether the prompt includes any
# configured perspective keyword. Stateless: parallel per-perspective calls each
# pass independently.

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty')

# Allow when project context is missing or subagent is not project-researcher
[ -z "$PROJECT_DIR" ] && exit 0
[ "$SUBAGENT_TYPE" = "project-researcher" ] || exit 0

# Load engine config
ENGINE_CONFIG="$PROJECT_DIR/.claude/engine.env"
if [ -f "$ENGINE_CONFIG" ]; then
  # shellcheck source=/dev/null
  . "$ENGINE_CONFIG"
fi

# No enforcement when the variable is unset or empty
[ -n "${RESEARCH_PERSPECTIVES:-}" ] || exit 0

# Case-insensitive check: does the prompt contain any perspective keyword?
PROMPT_LC=$(printf '%s' "$PROMPT" | tr '[:upper:]' '[:lower:]')
MATCHED=0
IFS=',' read -r -a PERSPECTIVES <<< "$RESEARCH_PERSPECTIVES"
for P in "${PERSPECTIVES[@]}"; do
  P_TRIM=$(echo "$P" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$P_TRIM" ] && continue
  P_LC=$(printf '%s' "$P_TRIM" | tr '[:upper:]' '[:lower:]')
  case "$PROMPT_LC" in
    *"$P_LC"*) MATCHED=1; break ;;
  esac
done

if [ "$MATCHED" -eq 1 ]; then
  exit 0
fi

# Block with guidance
AGENT_LINES=""
for P in "${PERSPECTIVES[@]}"; do
  P_TRIM=$(echo "$P" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$P_TRIM" ] && continue
  AGENT_LINES="${AGENT_LINES}
- project-researcher (perspective: ${P_TRIM})"
done

cat >&2 <<EOF
RESEARCH_PERSPECTIVES enforcement: single-perspective project-researcher call blocked.
Dispatch project-researcher in parallel, one call per perspective. Add
'Perspective: <name>' to each call's prompt.

Required parallel dispatches:${AGENT_LINES}
EOF
exit 2
