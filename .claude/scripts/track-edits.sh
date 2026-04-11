#!/bin/bash
# PostToolUse(Write|Edit) hook: 수정 파일 추적 + work-reviewer 제안
# additionalContext JSON으로 Claude 컨텍스트에 주입

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"

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

# work-reviewer 카운트: 자동 생성 경로 전체 제외 (sessions/, meta/, feeds/)
REVIEW_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  REVIEW_COUNT=$(grep -cvE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null || echo "0")
fi

# 수정 파일 목록 추출 (sessions/meta/feeds 제외)
EDITED_LIST=""
if [ -f "$EDITED_FILES" ]; then
  EDITED_LIST=$(grep -vE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null | head -20 | tr '\n' ', ' | sed 's/,$//')
fi

# Load engine config
ENGINE_CONFIG="$PROJECT_DIR/.claude/engine.config"
if [ -f "$ENGINE_CONFIG" ]; then
  # shellcheck source=/dev/null
  . "$ENGINE_CONFIG"
fi
REVIEW_THRESHOLD_SINGLE="${REVIEW_THRESHOLD_SINGLE:-2}"
REVIEW_THRESHOLD_MULTI="${REVIEW_THRESHOLD_MULTI:-5}"

# 인프라 파일 감지: .json, .yaml, .yml, .sh, .toml, Dockerfile 등 설정 위치
INFRA_COUNT=0
if [ -f "$EDITED_FILES" ]; then
  INFRA_COUNT=$(grep -vE '\.claude/(sessions|meta|feeds)/' "$EDITED_FILES" 2>/dev/null \
    | grep -cE '\.(json|yaml|yml|sh|toml)$|Dockerfile|settings\.' 2>/dev/null || echo "0")
fi

# 관점별 리뷰 메시지 생성
build_review_msg() {
  local count="$1" list="$2" multi="$3"
  if [ "$multi" = true ] && [ -n "${REVIEW_AGENTS:-}" ]; then
    # REVIEW_AGENTS 설정 시: 관점별 병렬 리뷰
    local agent_lines=""
    IFS=',' read -r -a PERSPECTIVES <<< "$REVIEW_AGENTS"
    for P in "${PERSPECTIVES[@]}"; do
      P=$(echo "$P" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      agent_lines="${agent_lines}\\n- work-reviewer (관점: ${P})"
    done
    echo "${count}개 파일이 수정되었습니다 (${list}). 다음 관점별 병렬 리뷰를 실행하세요:${agent_lines}"
  elif [ "$multi" = true ]; then
    echo "${count}개 파일이 수정되었습니다 (${list}). 인프라/대규모 변경 감지: 완료 전 multi-review (2명 병렬 검토)를 실행하세요."
  else
    echo "${count}개 파일이 수정되었습니다 (${list}). 완료 전 work-reviewer 에이전트를 실행하세요."
  fi
}

# 단계적 리뷰 제안
if [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_MULTI" ] || { [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_SINGLE" ] && [ "$INFRA_COUNT" -ge 1 ]; }; then
  MSG=$(build_review_msg "$REVIEW_COUNT" "$EDITED_LIST" true)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$MSG"
  }
}
EOF
elif [ "$REVIEW_COUNT" -ge "$REVIEW_THRESHOLD_SINGLE" ]; then
  MSG=$(build_review_msg "$REVIEW_COUNT" "$EDITED_LIST" false)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$MSG"
  }
}
EOF
fi

exit 0
