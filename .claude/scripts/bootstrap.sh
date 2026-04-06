#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

TARGET_DIR=""
DRY_RUN=0

usage() {
  cat <<'EOF'
사용법:
  .claude/scripts/bootstrap.sh --target <project-path> [--dry-run]

설명:
  새 프로젝트에 Claude Code 하네스 환경을 설치합니다.
  sync.sh로 관리 파일을 복사하고 프로젝트 디렉터리를 생성합니다.
  프로젝트별 하네스는 첫 세션에서 /harness-engine으로 동적 생성합니다.

옵션:
  --dry-run  실제 파일을 생성하지 않고 결과만 표시
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

# Resolve to absolute path
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || fail "대상 디렉터리가 존재하지 않습니다: $TARGET_DIR"

echo "========================================"
echo "  Claude Code Harness Bootstrap"
echo "========================================"
echo ""
echo "TARGET   $TARGET_DIR"
echo ""

# Step 1: sync managed files
echo "--- Step 1: 관리 파일 동기화 ---"
SYNC_ARGS="--source $SOURCE_DIR --target $TARGET_DIR"
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

# Step 3: create minimal settings.local.json if not exists
SETTINGS_LOCAL="$TARGET_DIR/.claude/settings.local.json"
if [ ! -f "$SETTINGS_LOCAL" ]; then
  echo "CREATE .claude/settings.local.json"
  if [ "$DRY_RUN" -eq 0 ]; then
    cat > "$SETTINGS_LOCAL" <<'EOJSON'
{
  "permissions": {
    "allow": [
      "Bash(ls:*)",
      "Bash(git:*)"
    ],
    "deny": [
      "Bash(git commit --no-verify*)",
      "Bash(git commit * --no-verify*)"
    ]
  }
}
EOJSON
  fi
else
  echo "SKIP .claude/settings.local.json (이미 존재)"
fi

# Step 4: create .gitignore additions if needed
GITIGNORE="$TARGET_DIR/.gitignore"
if [ "$DRY_RUN" -eq 0 ] && [ -f "$GITIGNORE" ]; then
  for pattern in ".claude/sessions/" ".claude/agent-memory/" ".claude/meta/" "temps/"; do
    if ! grep -Fqx "$pattern" "$GITIGNORE" 2>/dev/null; then
      echo "$pattern" >> "$GITIGNORE"
      echo "APPEND .gitignore: $pattern"
    fi
  done
fi

# Step 5: guidance
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
echo "  2. 첫 세션에서 하네스 생성"
echo "     claude"
echo "     > \"/harness-engine\""
echo "     harness-engine이 프로젝트 스택을 감지하고 맞춤 하네스를 생성합니다."
echo ""
echo "  도움말: .claude/docs/GETTING-STARTED.md"
echo "         (또는 ~/.claude-harness/.claude/docs/GETTING-STARTED.md)"
echo ""
