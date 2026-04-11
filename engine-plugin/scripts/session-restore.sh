#!/bin/bash
# SessionStart hook: 세션 상태/컨텍스트/플랜 복원
# --compact 플래그: 압축 후 추가 안내 메시지 포함

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
SESSION_ID_VAL="${SESSION_ID:-$(echo "$INPUT" | jq -r '.session_id // empty')}"

[ -z "$SESSION_ID_VAL" ] && exit 0

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID_VAL"
[ -d "$SESSION_DIR" ] || exit 0

# 프로젝트 디렉토리 자동 생성
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
  echo '위 플랜 파일을 Read하여 현재 작업 방향을 확인하세요.'
fi

if [ "$COMPACT_MODE" = true ]; then
  echo ''
  echo '> 컨텍스트에 ## Outcome 헤딩이 없으면 자동 추출된 raw 요약이다. 핵심만 추출: 달성한 것, 주요 결정, 다음 단계.'
fi

# Engine config 주입 (설정이 있으면 세션 시작 시 Claude에 알림)
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
    printf '프로젝트 설정 (.claude/engine.config):%s\n' "$CONFIG_ITEMS"
    if [ -n "${RESEARCH_PERSPECTIVES:-}" ]; then
      echo ''
      echo "조사 요청 시 project-researcher를 관점별(${RESEARCH_PERSPECTIVES})로 병렬 호출하세요."
    fi
  fi
fi

exit 0
