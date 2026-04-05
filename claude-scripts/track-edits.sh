#!/bin/bash
# PostToolUse(Write|Edit) hook: 수정 파일 추적 + work-reviewer 제안
# additionalContext JSON으로 Claude 컨텍스트에 주입

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty')

# SESSION_ID 없으면 추적하지 않음
if [ -z "$SESSION_ID" ] || [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
EDITED_FILES="$SESSION_DIR/.edited-files"

# 세션 디렉터리 확인
mkdir -p "$SESSION_DIR"

# 파일 경로 추가 (중복 방지) — 모든 편집 기록 (스냅샷 + 리뷰어 공용)
if [ -n "$FILE_PATH" ]; then
  if ! grep -qxF "$FILE_PATH" "$EDITED_FILES" 2>/dev/null; then
    echo "$FILE_PATH" >> "$EDITED_FILES"
  fi
fi

# work-reviewer 카운트: 자동 생성 파일만 제외 (SESSION.md, .edited-files 등)
REVIEW_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  REVIEW_COUNT=$(grep -cvE '\.claude/sessions/.*/(SESSION\.md|\.edited-files|\.plan-review-count)' "$EDITED_FILES" 2>/dev/null || echo "0")
fi

# 3개 이상이면 work-reviewer 제안
if [ "$REVIEW_COUNT" -ge 3 ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${REVIEW_COUNT}개 파일이 수정되었습니다. 완료 전 work-reviewer 에이전트를 실행하세요."
  }
}
EOF
fi

exit 0
