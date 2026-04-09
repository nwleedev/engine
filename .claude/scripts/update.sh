#!/bin/sh
# update.sh — 설치된 하네스를 최신 엔진 버전으로 업데이트
#
# 프로젝트 디렉터리에서 실행:
#   bash .claude/scripts/update.sh [--source <로컬경로>] [--dry-run] [--check]
#
# install.sh를 다시 실행하지 않고도 프로젝트의 하네스 파일을 갱신한다.
# sync.sh를 내부적으로 호출하여 매니페스트 기반 동기화를 수행한다.

set -eu

# --- Configuration ---
REPO="nwleedev/engine"
SOURCE_DIR=""
VERSION=""
DRY_RUN=0
CHECK_ONLY=0

# --- Detect project root ---
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$PROJECT_DIR/.claude/meta/manifest.json"
SYNC_SCRIPT="$PROJECT_DIR/.claude/scripts/sync.sh"

# --- Helpers ---
fail() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
사용법:
  bash .claude/scripts/update.sh [옵션]

설명:
  설치된 하네스를 최신 엔진 버전으로 업데이트합니다.
  sync.sh를 내부적으로 호출하여 변경된 파일만 갱신합니다.

옵션:
  --source <path>  로컬 엔진 소스 경로 (기본: GitHub에서 다운로드)
  --version <tag>  특정 버전으로 업데이트 (기본: main 최신)
  --check          업데이트 가능 여부만 확인 (파일 변경 없음)
  --dry-run        변경 미리보기 (파일 변경 없음)
  --help           도움말

예시:
  # 업데이트 확인만
  bash .claude/scripts/update.sh --check

  # 변경 미리보기
  bash .claude/scripts/update.sh --dry-run

  # 최신 버전으로 업데이트
  bash .claude/scripts/update.sh

  # 로컬 엔진 레포에서 오프라인 업데이트
  bash .claude/scripts/update.sh --source ~/engine

  # 특정 버전으로 업데이트
  bash .claude/scripts/update.sh --version v1.2.0
EOF
}

# --- Argument Parsing ---
while [ $# -gt 0 ]; do
  case "$1" in
    --source)
      [ $# -ge 2 ] || fail "--source 값이 없습니다."
      SOURCE_DIR="$2"
      shift 2
      ;;
    --version|-v)
      [ $# -ge 2 ] || fail "--version 값이 없습니다."
      VERSION="$2"
      shift 2
      ;;
    --check)
      CHECK_ONLY=1
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

# --- Validate ---
if [ ! -f "$MANIFEST" ]; then
  fail "하네스가 설치되지 않았습니다. (.claude/meta/manifest.json 없음)
  먼저 install.sh로 설치하세요."
fi

if [ ! -f "$SYNC_SCRIPT" ]; then
  fail "sync.sh를 찾을 수 없습니다: $SYNC_SCRIPT"
fi

# --- Read current version ---
current_commit=$(awk -F'"' '/"last_synced_commit"/ {print $4}' "$MANIFEST")

# --- Check mode ---
if [ "$CHECK_ONLY" -eq 1 ]; then
  if ! command -v curl >/dev/null 2>&1; then
    fail "'curl'이 설치되어 있지 않습니다. --check 모드에는 curl이 필요합니다."
  fi

  echo "현재 설치 버전: ${current_commit:-unknown}"

  if [ "$current_commit" = "unknown" ]; then
    echo ""
    echo "버전 정보가 없습니다 (이전 업데이트가 타볼 다운로드로 수행됨)."
    echo "업데이트 가능 여부를 확인하려면 --source 옵션으로 로컬 레포를 지정하세요."
    echo "또는 바로 업데이트를 실행하세요: bash .claude/scripts/update.sh"
    exit 0
  fi

  # GitHub API에서 최신 커밋 해시 조회 — current_commit 길이에 맞춰 비교
  commit_len=${#current_commit}
  latest_commit=$(curl -sL "https://api.github.com/repos/${REPO}/commits/main" \
    | awk -F'"' -v len="$commit_len" '/"sha"/ {print substr($4,1,len); exit}') || true

  if [ -z "$latest_commit" ]; then
    fail "GitHub API 조회 실패. 네트워크를 확인하세요."
  fi

  if [ "$current_commit" = "$latest_commit" ]; then
    echo "최신 버전입니다."
    exit 0
  else
    echo "업데이트 가능: ${current_commit} → ${latest_commit}"
    echo ""
    echo "미리보기: bash .claude/scripts/update.sh --dry-run"
    echo "업데이트: bash .claude/scripts/update.sh"
    exit 0
  fi
fi

# --- Prepare source ---
WORK_DIR=""
cleanup() {
  if [ -n "$WORK_DIR" ] && [ -d "$WORK_DIR" ]; then
    rm -rf "$WORK_DIR"
  fi
}
trap cleanup EXIT

if [ -n "$SOURCE_DIR" ]; then
  # 로컬 소스 사용
  SOURCE_DIR="$(cd "$SOURCE_DIR" 2>/dev/null && pwd)" || fail "소스 디렉터리가 존재하지 않습니다: $SOURCE_DIR"
  if [ ! -f "$SOURCE_DIR/.claude/CLAUDE.md.example" ]; then
    fail "유효한 엔진 레포가 아닙니다: $SOURCE_DIR (.claude/CLAUDE.md.example 없음)"
  fi
  echo "소스: $SOURCE_DIR (로컬)"
else
  # GitHub에서 다운로드
  for cmd in curl tar; do
    command -v "$cmd" >/dev/null 2>&1 || fail "'$cmd'이(가) 설치되어 있지 않습니다."
  done

  if [ -n "$VERSION" ]; then
    ARCHIVE_URL="https://github.com/${REPO}/archive/refs/tags/${VERSION}.tar.gz"
  else
    ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"
  fi

  WORK_DIR=$(mktemp -d)
  echo "소스: GitHub (${VERSION:-main})"
  echo "다운로드 중..."

  HTTP_CODE=$(curl -sL -w '%{http_code}' -o "$WORK_DIR/archive.tar.gz" "$ARCHIVE_URL" 2>/dev/null) || true
  case "$HTTP_CODE" in
    2[0-9][0-9]) ;;
    *) fail "다운로드 실패: $ARCHIVE_URL (HTTP $HTTP_CODE)" ;;
  esac

  if [ ! -s "$WORK_DIR/archive.tar.gz" ]; then
    fail "다운로드된 파일이 비어 있습니다."
  fi

  tar -xzf "$WORK_DIR/archive.tar.gz" --strip-components=1 -C "$WORK_DIR" \
    || fail "타볼 압축 해제에 실패했습니다."

  SOURCE_DIR="$WORK_DIR"
  echo "OK"
fi

# --- Run sync ---
echo ""
echo "========================================"
echo "  하네스 업데이트"
echo "========================================"
echo ""
echo "현재 버전: ${current_commit:-unknown}"
echo "대상: $PROJECT_DIR"
echo ""

SYNC_ARGS="--source $SOURCE_DIR --target $PROJECT_DIR"
if [ "$DRY_RUN" -eq 1 ]; then
  SYNC_ARGS="$SYNC_ARGS --dry-run"
fi

# sync.sh 실행 및 출력 캡처
# shellcheck disable=SC2086
sync_output=$(sh "$SYNC_SCRIPT" $SYNC_ARGS 2>&1)
sync_exit=$?
echo "$sync_output"

if [ "$sync_exit" -ne 0 ]; then
  echo ""
  echo "ERROR: sync.sh가 실패했습니다 (종료 코드: $sync_exit)."
  exit "$sync_exit"
fi

# --- Summary ---
create_count=$(printf '%s\n' "$sync_output" | grep -c '^CREATE' || true)
update_count=$(printf '%s\n' "$sync_output" | grep -c '^UPDATE' || true)
remove_count=$(printf '%s\n' "$sync_output" | grep -c '^REMOVE' || true)
merge_count=$(printf '%s\n' "$sync_output" | grep -c '^MERGE' || true)
conflict_count=$(printf '%s\n' "$sync_output" | grep -c '^CONFLICT' || true)

total_changes=$((create_count + update_count + remove_count + merge_count))

echo ""
echo "--- 업데이트 요약 ---"
if [ "$total_changes" -eq 0 ]; then
  echo "변경 없음. 이미 최신 상태입니다."
else
  [ "$create_count" -gt 0 ] && echo "  생성: ${create_count}개"
  [ "$update_count" -gt 0 ] && echo "  갱신: ${update_count}개"
  [ "$remove_count" -gt 0 ] && echo "  삭제: ${remove_count}개"
  [ "$merge_count" -gt 0 ]  && echo "  병합: ${merge_count}개"
  [ "$conflict_count" -gt 0 ] && echo "  충돌(건너뜀): ${conflict_count}개"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  echo "DRY RUN — 실제 변경 없음."
  echo "업데이트 실행: bash .claude/scripts/update.sh"
fi
