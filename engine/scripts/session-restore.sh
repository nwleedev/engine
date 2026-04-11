#!/bin/bash
# SessionStart hook: restore session state/context/plan
# --compact flag: includes additional guidance message after compaction

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
SESSION_ID_VAL="${SESSION_ID:-$(echo "$INPUT" | jq -r '.session_id // empty')}"

[ -z "$SESSION_ID_VAL" ] && exit 0

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID_VAL"
[ -d "$SESSION_DIR" ] || exit 0

# Auto-create project directories
mkdir -p "$PROJECT_DIR/.claude/plans" "$PROJECT_DIR/.claude/sessions" "$PROJECT_DIR/temps" 2>/dev/null

COMPACT_MODE=false
[ "$1" = "--compact" ] && COMPACT_MODE=true

if [ "$COMPACT_MODE" = true ]; then
  echo '## Session State (after compaction)'
else
  echo '## Session State'
fi

[ -f "$SESSION_DIR/SESSION.md" ] && cat "$SESSION_DIR/SESSION.md"

LATEST=$(ls -t "$SESSION_DIR/contexts/"CONTEXT-*.md 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  echo ''
  echo '## Latest Context Snapshot'
  cat "$LATEST"
fi

PLAN=$(ls -t "$PROJECT_DIR/.claude/plans/"*.md 2>/dev/null | head -1)
if [ -n "$PLAN" ]; then
  echo ''
  echo "## Active Plan: $PLAN"
  echo 'Read the above plan file to review the current work direction.'
fi

if [ "$COMPACT_MODE" = true ]; then
  echo ''
  echo '> If the context lacks a ## Outcome heading, it is an auto-extracted raw summary. Extract only the essentials: what was accomplished, key decisions, and next steps.'
fi

# Inject engine config (notify Claude at session start if config exists)
ENGINE_CONFIG="$PROJECT_DIR/.claude/engine.config"
if [ -f "$ENGINE_CONFIG" ]; then
  # shellcheck source=/dev/null
  . "$ENGINE_CONFIG"
  CONFIG_ITEMS=""
  [ -n "${REVIEW_AGENTS:-}" ] && CONFIG_ITEMS="${CONFIG_ITEMS}
- REVIEW_AGENTS=${REVIEW_AGENTS}"
  [ -n "${RESEARCH_PERSPECTIVES:-}" ] && CONFIG_ITEMS="${CONFIG_ITEMS}
- RESEARCH_PERSPECTIVES=${RESEARCH_PERSPECTIVES}"
  [ -n "${REVIEW_THRESHOLD_SINGLE:-}" ] && CONFIG_ITEMS="${CONFIG_ITEMS}
- REVIEW_THRESHOLD_SINGLE=${REVIEW_THRESHOLD_SINGLE}"
  [ -n "${REVIEW_THRESHOLD_MULTI:-}" ] && CONFIG_ITEMS="${CONFIG_ITEMS}
- REVIEW_THRESHOLD_MULTI=${REVIEW_THRESHOLD_MULTI}"
  if [ -n "$CONFIG_ITEMS" ]; then
    echo ''
    echo '## Engine Config'
    printf 'Project settings (.claude/engine.config):%s\n' "$CONFIG_ITEMS"
    if [ -n "${RESEARCH_PERSPECTIVES:-}" ]; then
      echo ''
      echo "When research is requested, invoke project-researcher in parallel by perspective (${RESEARCH_PERSPECTIVES})."
    fi
  fi
fi

exit 0
