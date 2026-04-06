#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
HARNESS_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

SOURCE_PROJECT=""
FILE_PATH=""
DESTINATION=""
DRY_RUN=0

usage() {
  cat <<'EOF'
사용법:
  promote.sh --source <project-path> --file <relative-path> [--destination core|reference] [--dry-run]

설명:
  프로젝트에서 만든 파일을 ~/.engine/에 승격합니다.

예시:
  # 범용 스킬을 코어에 승격
  promote.sh --source ~/my-api --file .claude/skills/core-auth-rules.md --destination core

  # 도메인 하네스를 harness-engine 예제로 승격
  promote.sh --source ~/my-api --file .claude/skills/harness-be-fastapi.md --destination reference

  # 스크립트를 코어에 승격
  promote.sh --source ~/my-api --file .claude/scripts/my-hook.sh --destination core

  # 자동 분류 (파일 경로 기반 추론)
  promote.sh --source ~/my-api --file .claude/skills/harness-be-fastapi.md

옵션:
  --destination core       코어 관리 파일로 승격 (sync 대상이 됨)
  --destination reference  harness-engine 예제로 승격
  --dry-run                실제 복사 없이 결과만 표시
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

# Infer destination from file path if not specified
infer_destination() {
  file="$1"

  case "$file" in
    # Domain harnesses → reference (harness-engine examples, never core)
    .claude/skills/harness-*)
      DESTINATION="reference"
      ;;
    # Core skills → core
    .claude/skills/*.md)
      DESTINATION="core"
      ;;
    # Agents → core
    .claude/agents/*)
      DESTINATION="core"
      ;;
    # Scripts → core
    .claude/scripts/*.sh)
      DESTINATION="core"
      ;;
    # Everything else → core
    *)
      DESTINATION="core"
      ;;
  esac
}

# Determine target path in harness repo
resolve_target() {
  file="$1"
  dest="$2"

  case "$dest" in
    core)
      # Direct mirror into harness repo
      echo "$HARNESS_DIR/$file"
      ;;
    reference)
      # Place under harness-engine examples
      basename_file=$(basename "$file")
      echo "$HARNESS_DIR/.claude/skills/harness-engine/references/examples/$basename_file"
      ;;
    *)
      fail "알 수 없는 destination: $dest"
      ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --source)
      [ $# -ge 2 ] || fail "--source 값이 없습니다."
      SOURCE_PROJECT="$2"
      shift 2
      ;;
    --file)
      [ $# -ge 2 ] || fail "--file 값이 없습니다."
      FILE_PATH="$2"
      shift 2
      ;;
    --destination)
      [ $# -ge 2 ] || fail "--destination 값이 없습니다."
      DESTINATION="$2"
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

[ -n "$SOURCE_PROJECT" ] || { usage; exit 1; }
[ -n "$FILE_PATH" ] || { usage; exit 1; }

# Resolve source project to absolute path
SOURCE_PROJECT="$(cd "$SOURCE_PROJECT" 2>/dev/null && pwd)" || fail "소스 프로젝트가 존재하지 않습니다."

# Validate source file exists
SRC_FILE="$SOURCE_PROJECT/$FILE_PATH"
[ -f "$SRC_FILE" ] || fail "소스 파일이 존재하지 않습니다: $SRC_FILE"

# Auto-infer destination if not specified
if [ -z "$DESTINATION" ]; then
  infer_destination "$FILE_PATH"
  echo "INFER destination=$DESTINATION (파일 경로 기반 추론)"
fi

# Resolve target path
DST_FILE=$(resolve_target "$FILE_PATH" "$DESTINATION")

echo ""
echo "========================================"
echo "  Promote"
echo "========================================"
echo ""
echo "FROM     $SRC_FILE"
echo "TO       $DST_FILE"
echo "MODE     $DESTINATION"
echo ""

# Check for conflicts
if [ -f "$DST_FILE" ]; then
  if cmp -s "$SRC_FILE" "$DST_FILE"; then
    echo "SKIP 동일한 파일이 이미 존재합니다."
    exit 0
  else
    echo "CONFLICT 대상에 다른 내용의 파일이 이미 존재합니다."
    echo ""
    echo "차이점:"
    diff "$DST_FILE" "$SRC_FILE" | head -20 || true
    echo ""
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "DRY RUN — 실제 덮어쓰기 안 함"
    else
      printf "덮어쓰시겠습니까? (y/N) "
      read -r answer
      case "$answer" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "취소됨."; exit 0 ;;
      esac
    fi
  fi
fi

# Copy
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN — 복사하지 않음"
else
  dst_dir=$(dirname "$DST_FILE")
  mkdir -p "$dst_dir"
  cp "$SRC_FILE" "$DST_FILE"

  # Preserve executable bit
  if [ -x "$SRC_FILE" ]; then
    chmod 755 "$DST_FILE"
  else
    chmod 644 "$DST_FILE"
  fi

  echo "DONE 승격 완료"
  echo ""
  echo "다음 단계:"
  echo "  cd $HARNESS_DIR"
  echo "  git diff"
  echo "  git add -A && git commit -m \"feat: promote $(basename "$FILE_PATH") from $(basename "$SOURCE_PROJECT")\""

  # Remind about whitelist if promoting a core script or agent
  case "$DESTINATION" in
    core)
      case "$FILE_PATH" in
        .claude/scripts/*.sh)
          echo ""
          echo "주의: 새 코어 스크립트가 sync 제외 목록에 포함되어 있는지 확인하세요."
          echo "  sync.sh → collect_source_paths() → grep -v 필터에 해당 파일이 없어야 동기화됩니다."
          ;;
        .claude/agents/*)
          echo ""
          echo "참고: 에이전트는 .claude/agents/ 하위 전체가 자동 동기화됩니다. 추가 작업 불필요."
          ;;
      esac
      ;;
  esac
fi
