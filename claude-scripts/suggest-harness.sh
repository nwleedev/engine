#!/bin/bash
# PostToolUse(Read) hook: 파일 내용 기반 harness 스킬 제안
# suggest-harness-patterns.json에서 패턴을 로드하여 프로젝트 무관하게 동작
# additionalContext JSON으로 Claude 컨텍스트에 주입

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 패턴 파일 로드 — 없으면 조용히 종료
PATTERNS_FILE="$CLAUDE_PROJECT_DIR/suggest-harness-patterns.json"
if [ ! -f "$PATTERNS_FILE" ]; then
  exit 0
fi

# file_glob으로 대상 파일 필터링
FILE_GLOB=$(jq -r '.file_glob // empty' "$PATTERNS_FILE")
if [ -n "$FILE_GLOB" ] && ! echo "$FILE_PATH" | grep -qE "$FILE_GLOB"; then
  exit 0
fi

# 파일 존재 확인
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# 테스트 파일 감지
IS_TEST=false
TEST_REGEX=$(jq -r '.test_regex // empty' "$PATTERNS_FILE")
if [ -n "$TEST_REGEX" ] && echo "$FILE_PATH" | grep -qE "$TEST_REGEX"; then
  IS_TEST=true
fi

CONTENT=$(head -100 "$FILE_PATH" 2>/dev/null)
SUGGESTIONS=""

# patterns 배열 순회하여 키워드 매칭
PATTERN_COUNT=$(jq '.patterns | length' "$PATTERNS_FILE")
i=0
while [ "$i" -lt "$PATTERN_COUNT" ]; do
  REGEX=$(jq -r ".patterns[$i].regex" "$PATTERNS_FILE")
  HARNESS=$(jq -r ".patterns[$i].harness" "$PATTERNS_FILE")
  LABEL=$(jq -r ".patterns[$i].label" "$PATTERNS_FILE")

  if echo "$CONTENT" | grep -qE "$REGEX"; then
    SUGGESTIONS="${SUGGESTIONS}• /${HARNESS} (${LABEL} 감지)\n"
  fi

  i=$((i + 1))
done

# 테스트 파일이면 test_harness 제안
if [ "$IS_TEST" = true ]; then
  TEST_HARNESS=$(jq -r '.test_harness // empty' "$PATTERNS_FILE")
  if [ -n "$TEST_HARNESS" ]; then
    SUGGESTIONS="${SUGGESTIONS}• /${TEST_HARNESS} (테스트 파일 감지)\n"
  fi
fi

# 제안이 있으면 additionalContext로 출력
if [ -n "$SUGGESTIONS" ]; then
  MSG="관련 harness 스킬이 감지되었습니다. 편집 전 해당 스킬을 호출하세요:\n${SUGGESTIONS}"
  ESCAPED_MSG=$(echo -e "$MSG" | jq -Rs .)
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": ${ESCAPED_MSG}
  }
}
EOF
fi

exit 0
