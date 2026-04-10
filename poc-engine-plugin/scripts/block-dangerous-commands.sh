#!/bin/bash
# PreToolUse(Bash) hook: 파괴적 git 명령 차단
# permissions.deny 대체: exit 2 = 차단 (stderr → Claude에게 전달)

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$COMMAND" ] && exit 0

# 차단 패턴 검사
case "$COMMAND" in
  *"git commit"*"--no-verify"*)
    echo "차단: --no-verify 플래그는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git push"*"--force"*)
    echo "차단: --force push는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git push"*-f*)
    echo "차단: force push (-f)는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git reset"*"--hard"*)
    echo "차단: git reset --hard는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git clean"*"-f"*)
    echo "차단: git clean -f는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git branch"*"-D"*)
    echo "차단: git branch -D는 사용할 수 없습니다" >&2
    exit 2
    ;;
  *"git checkout -- ."*)
    echo "차단: git checkout -- .는 사용할 수 없습니다" >&2
    exit 2
    ;;
esac

exit 0
