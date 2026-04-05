#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

TARGET_DIR=""
CATEGORY=""
DRY_RUN=0

usage() {
  cat <<'EOF'
사용법:
  bootstrap.sh --target <project-path> --category <category> [--dry-run]

설명:
  새 프로젝트에 Claude Code 하네스 환경을 설치합니다.
  sync.sh로 관리 파일을 복사한 뒤, 카테고리 템플릿을 1회 스탬핑합니다.

카테고리:
  dev-frontend         React, Vue, Next.js 등 프론트엔드
  dev-backend-python   FastAPI, Django, Flask 등
  dev-backend-go       Go 서버, CLI 도구
  non-dev-research     시장조사, 경쟁분석, 기술조사
  non-dev-marketing    마케팅 캠페인, 광고
  non-dev-design-doc   설계 문서, RFC, ADR
  non-dev-learning     기술 학습, 도메인 스터디

옵션:
  --dry-run            실제 파일을 생성하지 않고 결과만 표시
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ $# -ge 2 ] || fail "--target 값이 없습니다."
      TARGET_DIR="$2"
      shift 2
      ;;
    --category)
      [ $# -ge 2 ] || fail "--category 값이 없습니다."
      CATEGORY="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "알 수 없는 옵션입니다: $1"
      ;;
  esac
done

[ -n "$TARGET_DIR" ] || { usage; exit 1; }
[ -n "$CATEGORY" ] || { usage; exit 1; }

# Resolve to absolute path
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || fail "대상 디렉터리가 존재하지 않습니다: $TARGET_DIR"

# Validate category — template directory must exist (or will be created later)
TEMPLATE_DIR="$SOURCE_DIR/templates/$CATEGORY"
HAS_TEMPLATE=0
if [ -d "$TEMPLATE_DIR" ]; then
  HAS_TEMPLATE=1
fi

echo "========================================"
echo "  Claude Code Harness Bootstrap"
echo "========================================"
echo ""
echo "TARGET   $TARGET_DIR"
echo "CATEGORY $CATEGORY"
echo "TEMPLATE $([ "$HAS_TEMPLATE" -eq 1 ] && echo "$TEMPLATE_DIR" || echo "(없음 — 코어만 설치)")"
echo ""

# Step 1: sync managed files
echo "--- Step 1: 관리 파일 동기화 ---"
SYNC_ARGS="--source $SOURCE_DIR --target $TARGET_DIR"
if [ "$HAS_TEMPLATE" -eq 1 ]; then
  SYNC_ARGS="$SYNC_ARGS --template $CATEGORY"
fi
if [ "$DRY_RUN" -eq 1 ]; then
  SYNC_ARGS="$SYNC_ARGS --dry-run"
fi
# shellcheck disable=SC2086
sh "$SCRIPT_DIR/sync.sh" $SYNC_ARGS

# Step 2: create project directories
echo ""
echo "--- Step 2: 프로젝트 디렉터리 생성 ---"
for dir in .claude/plans .claude/sessions temps; do
  target_subdir="$TARGET_DIR/$dir"
  if [ -d "$target_subdir" ]; then
    echo "SKIP $dir (이미 존재)"
  else
    echo "CREATE $dir/"
    if [ "$DRY_RUN" -eq 0 ]; then
      mkdir -p "$target_subdir"
    fi
  fi
done

# Step 3: create .gitignore additions if needed
GITIGNORE="$TARGET_DIR/.gitignore"
if [ "$DRY_RUN" -eq 0 ]; then
  # Ensure essential ignores exist
  for pattern in ".claude/sessions/" ".claude/agent-memory/" "temps/" ".harness-sync-manifest.json"; do
    if [ -f "$GITIGNORE" ]; then
      if ! grep -Fqx "$pattern" "$GITIGNORE" 2>/dev/null; then
        echo "$pattern" >> "$GITIGNORE"
        echo "APPEND .gitignore: $pattern"
      fi
    fi
  done
fi

# Step 4: guidance
echo ""
echo "========================================"
echo "  설치 완료"
echo "========================================"
echo ""
echo "다음 단계:"
echo ""
echo "  1. CLAUDE.md 프로젝트 영역 작성"
echo "     <!-- HARNESS-SYNC-PROJECT-START --> 아래에 프로젝트별 규칙 추가"
echo ""

if echo "$CATEGORY" | grep -q "^dev-"; then
  echo "  2. MCP 서버 설정"
  echo "     claude mcp add context7 -- npx -y @anthropic-ai/context7-mcp-server"
  echo ""
  echo "  3. 첫 세션에서 하네스 생성"
  echo "     claude"
  echo "     > \"/harness-engine\""
  echo ""
  echo "  4. Lefthook 설치 (pre-commit 있을 때)"
  echo "     npx lefthook install"
else
  echo "  2. MCP 서버 설정"
  if echo "$CATEGORY" | grep -q "research\|marketing"; then
    echo "     claude mcp add tavily -- npx -y @anthropic-ai/tavily-mcp-server"
  fi
  echo ""
  echo "  3. 첫 세션에서 하네스 생성"
  echo "     claude"
  echo "     > \"/harness-engine\""
fi

echo ""
echo "  도움말: ~/.claude-harness/docs/GETTING-STARTED.md"
echo ""
