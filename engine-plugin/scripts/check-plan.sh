#!/bin/bash
# PreToolUse(Write|Edit) hook: 플랜 없이 코딩 시작 차단
# Exit 0 = 허용, Exit 2 = 차단 (stderr → Claude에게 전달)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# .claude/ 내부 파일은 항상 허용 (플랜/세션/스킬 편집)
if echo "$FILE_PATH" | grep -qE '\.claude/'; then
  exit 0
fi

# temps/ 내부 파일은 항상 허용
if echo "$FILE_PATH" | grep -qE 'temps/'; then
  exit 0
fi

# lefthook.yml, package.json 등 설정 파일은 허용
if echo "$FILE_PATH" | grep -qE '(lefthook\.yml|\.eslintrc|eslint\.config|\.prettierrc|tsconfig)'; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(echo "$INPUT" | jq -r '.cwd // empty')}"
PLANS_DIR="${PROJECT_DIR}/.claude/plans"

# 플랜 디렉터리 존재 확인
if [ ! -d "$PLANS_DIR" ]; then
  echo "플랜 파일이 없습니다. .claude/plans/에 플랜을 먼저 작성하세요." >&2
  exit 2
fi

# 72시간(259200초) 이내에 수정된 플랜 파일이 있는지 확인
NOW=$(date +%s)
FOUND_RECENT=false

for plan_file in "$PLANS_DIR"/*.md; do
  [ -f "$plan_file" ] || continue
  MTIME=$(stat -f %m "$plan_file" 2>/dev/null || stat -c %Y "$plan_file" 2>/dev/null)
  if [ -n "$MTIME" ]; then
    AGE=$(( NOW - MTIME ))
    if [ "$AGE" -lt 259200 ]; then
      FOUND_RECENT=true
      break
    fi
  fi
done

if [ "$FOUND_RECENT" = false ]; then
  echo "최근 72시간 이내에 수정된 플랜 파일이 없습니다. 플랜을 먼저 작성하거나 업데이트하세요." >&2
  exit 2
fi

exit 0
