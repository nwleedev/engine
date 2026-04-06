#!/bin/sh
set -eu

echo "경고: migrate.sh는 v1->v2 전환용이며 2026-07-01 이후 제거 예정입니다."
echo "      신규 설치는 install.sh를 사용하세요."
echo ""

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

TARGET_DIR=""
DRY_RUN=0

usage() {
  cat <<'EOF'
사용법:
  .claude/scripts/migrate.sh --target <project-path> [--dry-run]

설명:
  기존 레이아웃(claude-scripts/)을 새 레이아웃(.claude/scripts/)으로 마이그레이션합니다.

단계:
  1. 레이아웃 감지 (claude-scripts/ → 구 레이아웃)
  2. claude-scripts/*.sh → .claude/scripts/ 이동
  3. .claude/settings.json 훅 경로 업데이트
  4. suggest-harness-patterns.json 제거 (matchPatterns 프론트매터로 대체됨)
  5. 빈 claude-scripts/ 디렉터리 제거
  6. sync.sh 실행하여 최신 코어 파일 동기화

옵션:
  --dry-run  실제 변경 없이 결과만 표시
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

log_action() {
  printf '%s %s\n' "$1" "$2"
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
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || fail "대상 디렉터리가 존재하지 않습니다."

echo "========================================"
echo "  Harness Migration"
echo "========================================"
echo ""
echo "TARGET   $TARGET_DIR"
echo ""

# Step 1: Detect layout
OLD_SCRIPTS="$TARGET_DIR/claude-scripts"
NEW_SCRIPTS="$TARGET_DIR/.claude/scripts"

if [ -d "$NEW_SCRIPTS" ] && [ ! -d "$OLD_SCRIPTS" ]; then
  echo "이미 새 레이아웃(.claude/scripts/)입니다. 마이그레이션 불필요."
  exit 0
fi

if [ ! -d "$OLD_SCRIPTS" ]; then
  echo "claude-scripts/ 디렉터리가 없습니다. 부트스트랩부터 실행하세요:"
  echo "  ~/.engine/.claude/scripts/bootstrap.sh --target $TARGET_DIR"
  exit 1
fi

echo "--- Step 1: 구 레이아웃 감지 ---"
echo "DETECT claude-scripts/ (구 레이아웃)"

# Step 2: Move scripts
echo ""
echo "--- Step 2: 스크립트 이동 ---"

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$NEW_SCRIPTS"
fi

for script in "$OLD_SCRIPTS"/*.sh; do
  [ -f "$script" ] || continue
  name=$(basename "$script")
  if [ -f "$NEW_SCRIPTS/$name" ]; then
    log_action "SKIP" ".claude/scripts/$name (이미 존재)"
  else
    log_action "MOVE" "claude-scripts/$name → .claude/scripts/$name"
    if [ "$DRY_RUN" -eq 0 ]; then
      mv "$script" "$NEW_SCRIPTS/$name"
    fi
  fi
done

# Step 3: Update settings.json hook paths
echo ""
echo "--- Step 3: settings.json 훅 경로 업데이트 ---"

SETTINGS="$TARGET_DIR/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  if grep -q 'claude-scripts/' "$SETTINGS"; then
    log_action "UPDATE" ".claude/settings.json (claude-scripts/ → .claude/scripts/)"
    if [ "$DRY_RUN" -eq 0 ]; then
      sed -i '' 's|claude-scripts/|.claude/scripts/|g' "$SETTINGS"
    fi
  else
    log_action "SKIP" ".claude/settings.json (이미 업데이트됨)"
  fi
else
  log_action "WARN" ".claude/settings.json 없음"
fi

# Step 4: Remove suggest-harness-patterns.json
echo ""
echo "--- Step 4: suggest-harness-patterns.json 처리 ---"

PATTERNS="$TARGET_DIR/suggest-harness-patterns.json"
if [ -f "$PATTERNS" ]; then
  log_action "REMOVE" "suggest-harness-patterns.json (matchPatterns 프론트매터로 대체됨)"
  if [ "$DRY_RUN" -eq 0 ]; then
    rm "$PATTERNS"
  fi
else
  log_action "SKIP" "suggest-harness-patterns.json (없음)"
fi

# Step 5: Remove empty old directory
echo ""
echo "--- Step 5: 구 디렉터리 정리 ---"

if [ -d "$OLD_SCRIPTS" ]; then
  remaining=$(find "$OLD_SCRIPTS" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$remaining" -eq 0 ]; then
    log_action "REMOVE" "claude-scripts/ (빈 디렉터리)"
    if [ "$DRY_RUN" -eq 0 ]; then
      rmdir "$OLD_SCRIPTS" 2>/dev/null || true
    fi
  else
    log_action "WARN" "claude-scripts/에 프로젝트 고유 스크립트 ${remaining}개 남음 (수동 이동 필요)"
    if [ "$DRY_RUN" -eq 0 ]; then
      find "$OLD_SCRIPTS" -type f | sed 's/^/  /'
    fi
  fi
fi

# Step 6: Sync latest core files
echo ""
echo "--- Step 6: 최신 코어 파일 동기화 ---"

SYNC_SCRIPT="$SOURCE_DIR/.claude/scripts/sync.sh"
if [ -f "$SYNC_SCRIPT" ]; then
  SYNC_ARGS="--source $SOURCE_DIR --target $TARGET_DIR"
  if [ "$DRY_RUN" -eq 1 ]; then
    SYNC_ARGS="$SYNC_ARGS --dry-run"
  fi
  # shellcheck disable=SC2086
  sh "$SYNC_SCRIPT" $SYNC_ARGS
else
  log_action "WARN" "harness 저장소의 sync.sh를 찾을 수 없습니다: $SYNC_SCRIPT"
fi

echo ""
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN 완료"
else
  echo "마이그레이션 완료"
  echo ""
  echo "다음 단계:"
  echo "  1. 하네스 스킬에 matchPatterns 프론트매터가 있는지 확인"
  echo "     (없으면 description 키워드 폴백으로 동작)"
  echo "  2. claude를 실행하여 훅이 정상 동작하는지 확인"
fi
