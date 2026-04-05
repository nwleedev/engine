#!/bin/bash
# Stop/PreCompact hook: 자동 세션 스냅샷 생성
# Stop 훅에서는 실질적 작업이 있었을 때만, PreCompact에서는 항상 생��

INPUT=$(cat)

# 무한 루프 방지: 이미 Stop 훅이 활성화된 상태면 즉시 종료
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty')

# SESSION_ID 미설정 시 종료
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"

# 세션 디렉터리 없으면 생성
if [ ! -d "$SESSION_DIR" ]; then
  mkdir -p "$SESSION_DIR/contexts" "$SESSION_DIR/notes"
fi

EDITED_FILES="$SESSION_DIR/.edited-files"
HAS_EDITS=false
if [ -f "$EDITED_FILES" ] && [ -s "$EDITED_FILES" ]; then
  HAS_EDITS=true
fi

# Stop이면서 편집 없으면 건너뛰기 (단순 질문/답변 턴)
# --pre-compact이면 무조건 생성
if [ "$1" != "--pre-compact" ] && [ "$HAS_EDITS" = false ]; then
  exit 0
fi

# 스냅샷 데이터 수집
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
DATE_FILE=$(date +"%Y%m%d-%H%M")
LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' | head -c 20000)
TOOL_CALLS=$(echo "$INPUT" | jq -r '.tool_calls_made // 0')

# 수정된 파일 목록
FILES_LIST=""
if [ -f "$EDITED_FILES" ]; then
  FILES_LIST=$(sort -u "$EDITED_FILES" | head -20)
fi

# 플랜 경로
PLAN_FILE=""
if [ -d "$PROJECT_DIR/.claude/plans" ]; then
  PLAN_FILE=$(ls -t "$PROJECT_DIR/.claude/plans/"*.md 2>/dev/null | head -1)
fi

# 스냅샷 타입 결정
if [ "$1" = "--pre-compact" ]; then
  TITLE="pre-compact"
  SNAP_FILE="$SESSION_DIR/contexts/CONTEXT-${DATE_FILE}-pre-compact.md"
else
  TITLE="auto"
  SNAP_FILE="$SESSION_DIR/contexts/CONTEXT-${DATE_FILE}-auto.md"
fi

# contexts/ 디렉터리 확인
mkdir -p "$SESSION_DIR/contexts"

# 파일 수 집계
FILE_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  FILE_COUNT=$(wc -l < "$EDITED_FILES" | tr -d ' ')
fi

# 스냅샷 파일 생성 — 컨텍스트 압축 후 복구에 충분한 상세도
cat > "$SNAP_FILE" << SNAPEOF
# Snapshot: $TITLE
Date: $TIMESTAMP
Tool calls: $TOOL_CALLS | Files edited: $FILE_COUNT

## Files changed
$FILES_LIST

## Active plan
$PLAN_FILE

## Last response summary
$(echo "$LAST_MSG" | head -80)
SNAPEOF

# SESSION.md 생성 또는 업데이트
SESSION_MD="$SESSION_DIR/SESSION.md"

# SESSION.md 요약: 응답에서 첫 의미 있는 줄을 추출하여 Done 필드에 사용
DONE_LINE=$(echo "$LAST_MSG" | grep -v '^$' | grep -v '^#' | head -1 | head -c 120)
[ -z "$DONE_LINE" ] && DONE_LINE="(auto-snapshot)"

SUMMARY="### $TIMESTAMP — $TITLE
- Done: $DONE_LINE
- Files ($FILE_COUNT): $(echo "$FILES_LIST" | tr '\n' ', ' | sed 's/,$//')
- Tool calls: $TOOL_CALLS"

if [ ! -f "$SESSION_MD" ]; then
  # SESSION.md가 없으면 초기 생성
  cat > "$SESSION_MD" << SESSIONEOF
# Session Log

## Goal
(세션 목표 미설정)

## Active Decisions

## Snapshots (newest first)

$SUMMARY
SESSIONEOF
else
  # 기존 SESSION.md에 스냅샷 prepend
  TEMP_FILE=$(mktemp "$SESSION_DIR/.session-md-XXXXXX")
  {
    # Goal과 Active Decisions 섹션 유지
    sed -n '1,/^## Snapshots/p' "$SESSION_MD"
    echo ""
    echo "$SUMMARY"
    echo ""
    # 기존 스냅샷 유지
    sed -n '/^## Snapshots/,$ { /^## Snapshots/d; p; }' "$SESSION_MD"
  } > "$TEMP_FILE"

  # 80줄 제한
  head -80 "$TEMP_FILE" > "$SESSION_MD"
  rm -f "$TEMP_FILE"
fi

# 편집 파일 목록 초기화
if [ -f "$EDITED_FILES" ]; then
  > "$EDITED_FILES"
fi

exit 0
