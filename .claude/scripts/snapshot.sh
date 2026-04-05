#!/bin/bash
# Stop/PreCompact hook: 자동 세션 스냅샷 생성
# 3단계: pre-compact(항상), auto(편집 있을 때), mini(읽기만 있을 때)

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
READ_FILES="$SESSION_DIR/.read-files"

HAS_EDITS=false
if [ -f "$EDITED_FILES" ] && [ -s "$EDITED_FILES" ]; then
  HAS_EDITS=true
fi

HAS_READS=false
if [ -f "$READ_FILES" ] && [ -s "$READ_FILES" ]; then
  HAS_READS=true
fi

# 편집도 읽기도 없으면 건너뛰기 (단순 질문/답변 턴)
# --pre-compact이면 무조건 생성
if [ "$1" != "--pre-compact" ] && [ "$HAS_EDITS" = false ] && [ "$HAS_READS" = false ]; then
  exit 0
fi

# 스냅샷 데이터 수집
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
DATE_FILE=$(date +"%Y%m%d-%H%M")
TOOL_CALLS=$(echo "$INPUT" | jq -r '.tool_calls_made // 0')

# 턴 전체 텍스트 수집: transcript에서 최근 assistant 메시지들의 text를 결합
# last_assistant_message는 마지막 텍스트 블록만 포함하므로 부족
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')
LAST_MSG=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  LAST_MSG=$(tail -200 "$TRANSCRIPT_PATH" | jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "text") | .text' 2>/dev/null | tail -200 | head -c 20000)
fi
# transcript 파싱 실패 시 fallback
if [ -z "$LAST_MSG" ]; then
  LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' | head -c 20000)
fi

# 수정된 파일 목록
FILES_LIST=""
if [ -f "$EDITED_FILES" ]; then
  FILES_LIST=$(sort -u "$EDITED_FILES" | head -20)
fi

# 읽기 파일 목록
READS_LIST=""
if [ -f "$READ_FILES" ]; then
  READS_LIST=$(sort -u "$READ_FILES" | head -20)
fi

# 플랜 경로
PLAN_FILE=""
if [ -d "$PROJECT_DIR/.claude/plans" ]; then
  PLAN_FILE=$(ls -t "$PROJECT_DIR/.claude/plans/"*.md 2>/dev/null | head -1)
fi

# 스냅샷 타입 결정
IS_MINI=false
if [ "$1" = "--pre-compact" ]; then
  TITLE="pre-compact"
elif [ "$HAS_EDITS" = true ]; then
  TITLE="auto"
else
  # 편집 없이 읽기만 있는 턴 → mini-snapshot
  TITLE="mini"
  IS_MINI=true
fi
SNAP_FILE="$SESSION_DIR/contexts/CONTEXT-${DATE_FILE}-${TITLE}.md"

# contexts/ 디렉터리 확인
mkdir -p "$SESSION_DIR/contexts"

# 파일 수 집계
FILE_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  FILE_COUNT=$(wc -l < "$EDITED_FILES" | tr -d ' ')
fi
READ_COUNT=0
if [ -f "$READ_FILES" ]; then
  READ_COUNT=$(wc -l < "$READ_FILES" | tr -d ' ')
fi

# 스냅샷 파일 생성
cat > "$SNAP_FILE" << SNAPEOF
# Snapshot: $TITLE
Date: $TIMESTAMP
Tool calls: $TOOL_CALLS | Files edited: $FILE_COUNT | Files read: $READ_COUNT

## Files changed
$FILES_LIST

## Files read
$READS_LIST

## Active plan
$PLAN_FILE

## Last response summary
$(echo "$LAST_MSG" | head -80)
SNAPEOF

# SESSION.md 생성 또는 업데이트
SESSION_MD="$SESSION_DIR/SESSION.md"

# mini-snapshot은 contexts/에만 저장, SESSION.md는 건너뛰기 (80줄 보존)
if [ "$IS_MINI" = true ]; then
  # 파일 목록 초기화 (대칭성 유지)
  [ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
  [ -f "$READ_FILES" ] && > "$READ_FILES"
  exit 0
fi

# full/pre-compact: SESSION.md 업데이트
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

# 파일 목록 초기화
[ -f "$EDITED_FILES" ] && > "$EDITED_FILES"
[ -f "$READ_FILES" ] && > "$READ_FILES"

exit 0
