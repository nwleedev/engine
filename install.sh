#!/bin/sh
# Claude Code Harness Installer
# Usage: sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- <project-path>
set -eu

# --- Configuration ---
REPO="nwleedev/engine"
VERSION=""
TARGET_DIR=""

# --- Helpers ---
fail() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Claude Code Harness Installer

사용법:
  install.sh <project-path> [--version <tag>]

  # curl 원라이너
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- <project-path>

옵션:
  --version <tag>  설치할 버전 (기본: main 브랜치 최신)

사전 요건:
  curl, tar (jq는 선택: 훅 검증에 사용)
EOF
}

# --- Argument Parsing ---
while [ $# -gt 0 ]; do
  case "$1" in
    --version|-v)
      [ $# -ge 2 ] || fail "--version 값이 없습니다."
      VERSION="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    -*)
      fail "알 수 없는 옵션입니다: $1"
      ;;
    *)
      if [ -z "$TARGET_DIR" ]; then
        TARGET_DIR="$1"
      else
        fail "대상 디렉터리가 이미 지정되었습니다: $TARGET_DIR (추가: $1)"
      fi
      shift
      ;;
  esac
done

[ -n "$TARGET_DIR" ] || { usage; exit 1; }

# Resolve target to absolute path; create if not exists
if [ ! -d "$TARGET_DIR" ]; then
  mkdir -p "$TARGET_DIR"
fi
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# --- Dependency Check ---
for cmd in curl tar; do
  command -v "$cmd" >/dev/null 2>&1 || fail "'$cmd'이(가) 설치되어 있지 않습니다."
done

# --- Build Download URL ---
if [ -n "$VERSION" ]; then
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/tags/${VERSION}.tar.gz"
else
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"
fi

# --- Download & Extract ---
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

echo "========================================"
echo "  Claude Code Harness Installer"
echo "========================================"
echo ""
echo "TARGET   $TARGET_DIR"
echo "VERSION  ${VERSION:-main (latest)}"
echo ""

echo "--- 하네스 다운로드 ---"
HTTP_CODE=$(curl -sL -w '%{http_code}' -o "$WORK_DIR/archive.tar.gz" "$ARCHIVE_URL" 2>/dev/null) || true
case "$HTTP_CODE" in
  2[0-9][0-9]) ;;  # 2xx: success
  *) fail "다운로드 실패: $ARCHIVE_URL (HTTP $HTTP_CODE)" ;;
esac
if [ ! -s "$WORK_DIR/archive.tar.gz" ]; then
  fail "다운로드된 파일이 비어 있습니다: $ARCHIVE_URL"
fi
echo "OK ($ARCHIVE_URL)"

echo "--- 압축 해제 ---"
tar -xzf "$WORK_DIR/archive.tar.gz" --strip-components=1 -C "$WORK_DIR" \
  || fail "타볼 압축 해제에 실패했습니다."
echo "OK"
echo ""

# --- Run Bootstrap ---
BOOTSTRAP="$WORK_DIR/.claude/scripts/bootstrap.sh"
[ -f "$BOOTSTRAP" ] || fail "bootstrap.sh를 찾을 수 없습니다. 타볼 구조를 확인하세요."

sh "$BOOTSTRAP" --source "$WORK_DIR" --target "$TARGET_DIR"
