#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

TARGET_DIR=""
DRY_RUN=0
FORCE=0

usage() {
  cat <<'EOF'
사용법:
  bootstrap.sh --target <project-path> [--source <harness-root>] [--force] [--dry-run]

설명:
  새 프로젝트에 Claude Code 하네스 환경을 설치합니다.
  sync.sh로 관리 파일을 복사하고 프로젝트 디렉터리를 생성합니다.
  이미 설치된 프로젝트에서는 업데이트(sync)만 실행합니다.

옵션:
  --source   하네스 소스 디렉터리 (기본: 스크립트 위치 기준 자동 감지)
  --force    기존 설치가 있어도 전체 부트스트랩 재실행
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
    --source)
      [ $# -ge 2 ] || fail "--source 값이 없습니다."
      SOURCE_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
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

# Resolve to absolute paths
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || fail "대상 디렉터리가 존재하지 않습니다: $TARGET_DIR"
SOURCE_DIR="$(cd "$SOURCE_DIR" 2>/dev/null && pwd)" || fail "소스 디렉터리가 존재하지 않습니다: $SOURCE_DIR"

# Idempotency: if already installed, run sync only (unless --force)
if [ "$FORCE" -eq 0 ] && [ -f "$TARGET_DIR/.claude/meta/manifest.json" ]; then
  echo "기존 설치가 감지되었습니다. 업데이트를 실행합니다."
  echo "(전체 재설치: --force 플래그 사용)"
  echo ""
  SYNC_ARGS="--source $SOURCE_DIR --target $TARGET_DIR"
  if [ "$DRY_RUN" -eq 1 ]; then
    SYNC_ARGS="$SYNC_ARGS --dry-run"
  fi
  # shellcheck disable=SC2086
  sh "$SCRIPT_DIR/sync.sh" $SYNC_ARGS
  exit $?
fi

echo "========================================"
echo "  Claude Code Harness Bootstrap"
echo "========================================"
echo ""
echo "TARGET   $TARGET_DIR"
echo "SOURCE   $SOURCE_DIR"
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
  for pattern in ".claude/sessions/" ".claude/agent-memory/" ".claude/meta/" ".claude/feeds/" "temps/"; do
    if ! grep -Fqx "$pattern" "$GITIGNORE" 2>/dev/null; then
      echo "$pattern" >> "$GITIGNORE"
      echo "APPEND .gitignore: $pattern"
    fi
  done
fi

# Step 5: 훅-스크립트 존재 검증
SETTINGS_JSON="$TARGET_DIR/.claude/settings.json"
if [ -f "$SETTINGS_JSON" ] && command -v jq >/dev/null 2>&1; then
  HOOK_WARNINGS=0
  for script_path in $(jq -r '.. | .command? // empty' "$SETTINGS_JSON" 2>/dev/null \
    | grep -o 'scripts/[^"[:space:]]*' | sort -u); do
    resolved="$TARGET_DIR/.claude/$script_path"
    if [ ! -f "$resolved" ]; then
      echo "WARN 훅이 참조하는 스크립트가 없습니다: .claude/$script_path"
      HOOK_WARNINGS=$((HOOK_WARNINGS + 1))
    fi
  done
  if [ "$HOOK_WARNINGS" -eq 0 ]; then
    echo "CHECK 훅-스크립트 정합성 확인 완료"
  fi
fi

# Step 6: guidance
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
echo ""
