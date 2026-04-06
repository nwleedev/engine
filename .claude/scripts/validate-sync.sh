#!/bin/bash
# validate-sync.sh — sync.sh 화이트리스트와 실제 파일의 정합성 검증
# 종료 코드: 0 = 정상, 1 = 드리프트 감지
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_DIR="$SOURCE_DIR/.claude"
SYNC_SH="$CLAUDE_DIR/scripts/sync.sh"

ERRORS=0

red()   { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }

# --- 화이트리스트 파싱 (awk — 단일행/복수행 for 루프 모두 처리) ---
extract_for_items() {
  local var_name="$1"
  awk -v var="$var_name" '
    !collecting && $0 ~ ("for " var " in") {
      line = $0
      sub(".*for " var " in", "", line)
      if (line ~ /; *do/) {
        sub(/; *do.*/, "", line)
        print line
        next
      }
      sub(/\\[[:space:]]*$/, "", line)
      print line
      collecting = 1
      next
    }
    collecting {
      line = $0
      if (line ~ /; *do/) {
        sub(/; *do.*/, "", line)
        print line
        collecting = 0
        next
      }
      sub(/\\[[:space:]]*$/, "", line)
      print line
    }
  ' "$SYNC_SH" | tr -s '[:space:]' '\n' | sed '/^$/d' | sort
}

WL_SKILLS=$(extract_for_items "skill")
WL_AGENTS=$(extract_for_items "agent")
WL_SCRIPTS=$(extract_for_items "script")
WL_DOCS=$(extract_for_items "doc")

# --- 실제 파일 수집 ---

ACTUAL_SKILLS=$(cd "$CLAUDE_DIR" && ls skills/*.md 2>/dev/null \
  | sed 's|^skills/||' \
  | grep -v '^harness-' \
  | sort || true)

ACTUAL_AGENTS=$(cd "$CLAUDE_DIR" && ls agents/*/AGENT.md 2>/dev/null \
  | sed 's|^agents/||; s|/AGENT.md$||' \
  | sort || true)

ACTUAL_SCRIPTS=$(cd "$CLAUDE_DIR" && ls scripts/*.sh 2>/dev/null \
  | sed 's|^scripts/||' \
  | grep -v '^validate-sync\.sh$' \
  | sort || true)

ACTUAL_DOCS=$(cd "$CLAUDE_DIR" && ls docs/*.md 2>/dev/null \
  | sed 's|^docs/||' \
  | sort || true)

# --- 비교 ---
check_category() {
  local category="$1"
  local whitelist="$2"
  local actual="$3"
  local found_issue=0

  # 실제 존재 − 화이트리스트 = NOT IN WHITELIST
  while IFS= read -r item; do
    [ -n "$item" ] || continue
    if ! echo "$whitelist" | grep -Fqx "$item"; then
      red "  NOT IN WHITELIST: $category/$item"
      found_issue=1
    fi
  done <<< "$actual"

  # 화이트리스트 − 실제 존재 = STALE ENTRY
  while IFS= read -r item; do
    [ -n "$item" ] || continue
    if ! echo "$actual" | grep -Fqx "$item"; then
      red "  STALE ENTRY: $category/$item (파일 없음)"
      found_issue=1
    fi
  done <<< "$whitelist"

  if [ "$found_issue" -eq 0 ]; then
    green "  $category: OK"
  else
    ERRORS=1
  fi
}

# --- 실행 ---
echo "=== sync.sh 화이트리스트 정합성 검증 ==="
echo ""

echo "[skills]"
check_category "skills" "$WL_SKILLS" "$ACTUAL_SKILLS"
echo ""

echo "[agents]"
check_category "agents" "$WL_AGENTS" "$ACTUAL_AGENTS"
echo ""

echo "[scripts]"
check_category "scripts" "$WL_SCRIPTS" "$ACTUAL_SCRIPTS"
echo ""

echo "[docs]"
check_category "docs" "$WL_DOCS" "$ACTUAL_DOCS"
echo ""

if [ "$ERRORS" -eq 0 ]; then
  green "=== 모든 카테고리 정합성 확인 완료 ==="
else
  red "=== 드리프트 감지: sync.sh 화이트리스트 업데이트 필요 ==="
fi

exit "$ERRORS"
