#!/bin/bash
# PreToolUse(ExitPlanMode) hook: enforce plan review before exiting
# First call: block + present checklist, second call: allow

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

# Allow if SESSION_ID is missing
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
COUNTER_FILE="$SESSION_DIR/.plan-review-count"

mkdir -p "$SESSION_DIR"

# Find plan file path
PLANS_DIR="$PROJECT_DIR/.claude/plans"
PLAN_FILE=$(ls -t "$PLANS_DIR"/*.md 2>/dev/null | head -1)

# Detect unresolved options (checked regardless of counter)
if [ -n "$PLAN_FILE" ]; then
  HAS_OPTIONS=false
  if grep -qiE '## Options|## 선택지|### Option [A-Z]|^- \[ \] Option' "$PLAN_FILE" 2>/dev/null; then
    HAS_OPTIONS=true
  fi

  HAS_SELECTION=false
  if grep -qiE '\[선택됨\]|\[Selected\]|^- \[x\] Option|✓ Option|→ 선택:' "$PLAN_FILE" 2>/dev/null; then
    HAS_SELECTION=true
  fi

  if [ "$HAS_OPTIONS" = true ] && [ "$HAS_SELECTION" = false ]; then
    echo "The plan contains options but no user selection has been made." >&2
    echo "Ask the user to choose via AskUserQuestion, then record the selection in the plan." >&2
    echo "(e.g., add '→ Selected: Option A' or '[Selected]' marker)" >&2
    exit 2
  fi
fi

# Read counter
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
fi

if [ "$COUNT" -eq 0 ]; then
  # First attempt: block + present checklist
  echo "1" > "$COUNTER_FILE"

  # Check for required sections in the plan file
  MISSING=""

  if [ -n "$PLAN_FILE" ]; then
    if ! grep -qi '## Context\|## context' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Missing Context section"
    fi
    if ! grep -qi '## Changes\|## changes\|## Specific Changes\|변경' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Missing Changes section"
    fi
    if ! grep -qi '## Verification\|## verification\|검증' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Missing Verification section"
    fi
  fi

  MSG="Plan review is required. Please verify the following:
1. All target file paths actually exist
2. Assumptions are explicitly stated
3. Verification methods are specific
4. No items are missing"

  if [ -n "$MISSING" ]; then
    MSG="${MSG}

Required section check:$(echo -e "$MISSING")"
  fi

  echo "$MSG" >&2
  exit 2
else
  # Second attempt: allow + reset counter
  echo "0" > "$COUNTER_FILE"
  exit 0
fi
