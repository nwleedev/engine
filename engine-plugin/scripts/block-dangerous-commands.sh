#!/bin/bash
# PreToolUse(Bash) hook: block destructive git commands
# Replaces permissions.deny: exit 2 = block (stderr → forwarded to Claude)

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$COMMAND" ] && exit 0

# Check against blocked patterns
case "$COMMAND" in
  *"git commit"*"--no-verify"*)
    echo "Blocked: --no-verify flag is not allowed" >&2
    exit 2
    ;;
  *"git push"*"--force"*)
    echo "Blocked: --force push is not allowed" >&2
    exit 2
    ;;
  *"git push"*-f*)
    echo "Blocked: force push (-f) is not allowed" >&2
    exit 2
    ;;
  *"git reset"*"--hard"*)
    echo "Blocked: git reset --hard is not allowed" >&2
    exit 2
    ;;
  *"git clean"*"-f"*)
    echo "Blocked: git clean -f is not allowed" >&2
    exit 2
    ;;
  *"git branch"*"-D"*)
    echo "Blocked: git branch -D is not allowed" >&2
    exit 2
    ;;
  *"git checkout -- ."*)
    echo "Blocked: git checkout -- . is not allowed" >&2
    exit 2
    ;;
esac

exit 0
