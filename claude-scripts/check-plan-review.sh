#!/bin/bash
# PreToolUse(ExitPlanMode) hook: 플랜 반복 검토 강제
# 첫 호출 시 차단 + 체크리스트 제시, 두 번째 호출에서 허용

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty')

# SESSION_ID 없으면 허용
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
COUNTER_FILE="$SESSION_DIR/.plan-review-count"

mkdir -p "$SESSION_DIR"

# 카운터 읽기
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
fi

if [ "$COUNT" -eq 0 ]; then
  # 첫 번째 시도: 차단 + 체크리스트 제시
  echo "1" > "$COUNTER_FILE"

  # 플랜 파일에서 필수 섹션 확인
  PLANS_DIR="$PROJECT_DIR/.claude/plans"
  PLAN_FILE=$(ls -t "$PLANS_DIR"/*.md 2>/dev/null | head -1)
  MISSING=""

  if [ -n "$PLAN_FILE" ]; then
    if ! grep -qi '## Context\|## context' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Context 섹션 누락"
    fi
    if ! grep -qi '## Changes\|## changes\|## Specific Changes\|변경' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Changes 섹션 누락"
    fi
    if ! grep -qi '## Verification\|## verification\|검증' "$PLAN_FILE" 2>/dev/null; then
      MISSING="${MISSING}\n- Verification 섹션 누락"
    fi
  fi

  MSG="플랜 재검토가 필요합니다. 다음을 확인하세요:
1. 모든 변경 대상 파일 경로가 실제 존재하는가
2. 가정(assumptions)이 명시되어 있는가
3. 검증 방법이 구체적인가
4. 누락된 항목이 없는가"

  if [ -n "$MISSING" ]; then
    MSG="${MSG}

필수 섹션 검증:$(echo -e "$MISSING")"
  fi

  echo "$MSG" >&2
  exit 2
else
  # 두 번째 시도: 허용 + 카운터 초기화
  echo "0" > "$COUNTER_FILE"
  exit 0
fi
