#!/bin/bash
# PostToolUse(Read) hook: 파일 내용 기반 harness 스킬 제안
# .claude/skills/harness-*.md 프론트매터의 matchPatterns에서 패턴을 직접 로드
# 외부 설정 파일 불필요 — matchPatterns 없으면 description 키워드로 폴백
# additionalContext JSON으로 Claude 컨텍스트에 주입

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID_VAL=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_DIR_VAL=$(echo "$INPUT" | jq -r '.cwd // empty')

# 읽기 파일 추적 — snapshot.sh의 mini-snapshot 판단용
if [ -n "$SESSION_ID_VAL" ] && [ -n "$PROJECT_DIR_VAL" ] && [ -n "$FILE_PATH" ]; then
  READ_FILE="$PROJECT_DIR_VAL/.claude/sessions/$SESSION_ID_VAL/.read-files"
  mkdir -p "$(dirname "$READ_FILE")"
  if ! grep -qxF "$FILE_PATH" "$READ_FILE" 2>/dev/null; then
    echo "$FILE_PATH" >> "$READ_FILE"
  fi
fi

# 파일 존재 확인
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# 하네스 스킬 디렉터리 확인
SKILLS_DIR="$CLAUDE_PROJECT_DIR/.claude/skills"
if [ ! -d "$SKILLS_DIR" ]; then
  exit 0
fi

CONTENT=$(head -100 "$FILE_PATH" 2>/dev/null)
SUGGESTIONS=""
TMPFILE="/tmp/suggest-harness-$$.txt"
: > "$TMPFILE"

# 각 하네스 스킬 순회
for skill_file in "$SKILLS_DIR"/harness-*.md; do
  [ -f "$skill_file" ] || continue

  skill_name=$(basename "$skill_file" .md)

  # YAML 프론트매터 추출 (첫 번째 --- 이후 ~ 두 번째 --- 이전)
  frontmatter=$(sed -n '2,/^---$/p' "$skill_file" | sed '$d')

  # matchPatterns.fileGlob 추출
  file_glob=$(echo "$frontmatter" | sed -n 's/^  fileGlob: *"\(.*\)"/\1/p' | head -1)

  # fileGlob이 있으면 파일 경로 필터링
  if [ -n "$file_glob" ]; then
    if ! echo "$FILE_PATH" | grep -qE "$file_glob"; then
      continue
    fi
  fi

  # matchPatterns.regex 배열 추출
  regexes=$(echo "$frontmatter" | sed -n '/^  regex:/,/^[^ ]/p' | grep '^ *- ' | sed 's/^ *- *"\(.*\)"/\1/' | sed "s/^ *- *'\(.*\)'/\1/" | sed 's/^ *- *//')

  matched=false

  if [ -n "$regexes" ]; then
    # matchPatterns.regex로 매칭
    while IFS= read -r regex; do
      [ -n "$regex" ] || continue
      if echo "$CONTENT" | grep -qE "$regex"; then
        matched=true
        break
      fi
    done <<EOF_REGEX
$regexes
EOF_REGEX
  else
    # matchPatterns 없으면 description에서 키워드 추출하여 폴백
    description=$(echo "$frontmatter" | sed -n 's/^description: *//p' | head -1)
    keywords=$(echo "$description" | sed 's/.*— //; s/\. .*//' | tr ',' '\n' | sed 's/^ *//; s/ *$//' | grep -v '^$')

    if [ -n "$keywords" ]; then
      while IFS= read -r kw; do
        [ -n "$kw" ] || continue
        if echo "$CONTENT" | grep -qi "$kw"; then
          matched=true
          break
        fi
      done <<EOF_KW
$keywords
EOF_KW
    fi
  fi

  if [ "$matched" = true ]; then
    # label 추출
    label=$(echo "$frontmatter" | sed -n 's/^description: *Use when working with \(.*\) —.*/\1/p' | head -1)
    [ -z "$label" ] && label="$skill_name"
    printf '• /%s (%s 감지)\n' "$skill_name" "$label" >> "$TMPFILE"
  fi
done

SUGGESTIONS=$(cat "$TMPFILE" 2>/dev/null)
rm -f "$TMPFILE"

# 제안이 있으면 additionalContext로 출력
if [ -n "$SUGGESTIONS" ]; then
  MSG="관련 harness 스킬이 감지되었습니다. 편집 전 해당 스킬을 호출하세요:\n${SUGGESTIONS}\n"
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
