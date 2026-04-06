#!/bin/sh
# set -eu: -e는 명령이 실패(종료 코드 ≠ 0)하면 스크립트를 즉시 종료한다.
#          -u는 정의되지 않은 변수를 참조하면 오류를 발생시킨다.
set -eu

MANIFEST_FILE=".claude/meta/manifest.json"
OLD_MANIFEST_FILE=".harness-sync-manifest.json"
DRY_RUN=0
TARGET_DIR=""

# CDPATH= : CDPATH 환경변수를 비워서 cd가 예상치 못한 디렉터리로 이동하는 것을 방지한다.
# cd -- : --는 옵션 종료 표시로, 경로가 -로 시작해도 옵션으로 해석되지 않는다.
# dirname -- "$0" : 현재 스크립트 파일이 위치한 디렉터리 경로를 추출한다.
# && pwd : cd 성공 후 절대 경로를 출력한다.
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# 스크립트 위치(.claude/scripts/)에서 두 단계 상위로 이동하여 엔진(소스) 루트 디렉터리를 결정한다.
SOURCE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

usage() {
  # cat <<'EOF' : 작은따옴표로 감싼 히어독(heredoc)은 변수 치환 없이 문자열 그대로 출력한다.
  cat <<'EOF'
사용법:
  .claude/scripts/sync.sh --target <project-path> [--source <harness-source>] [--dry-run]

설명:
  현재 저장소의 하네스 자산을 다른 프로젝트에 설치하거나 업데이트합니다.
  프로젝트에 이미 존재하는 파일과 충돌 시 경고를 출력하고 건너뜁니다.

관리 대상 (디렉터리 단위 자동 수집):
  - CLAUDE.md (마커 기반 병합: .claude/CLAUDE.md.example → 프로젝트 루트 CLAUDE.md)
  - .claude/settings.json
  - .claude/scripts/**    (전체)
  - .claude/skills/**     (전체)
  - .claude/agents/**     (전체)
  - .claude/docs/**       (전체)

비관리 대상 (프로젝트 소유):
  - .claude/sessions/*, .claude/plans/*, .claude/agent-memory/*
  - .claude/settings.local.json
  - .claude/skills/harness-*.md  (프로젝트별 도메인 하네스)
  - .claude/meta/                (sync 메타데이터, 자동 생성)

충돌 처리:
  - 이전 sync로 관리된 파일(매니페스트에 등록된 파일)은 정상 업데이트합니다.
  - 프로젝트가 자체적으로 보유한 파일은 CONFLICT 경고 후 건너뜁니다.
  - CLAUDE.md는 마커 기반 병합으로 프로젝트 영역을 보존합니다.
EOF
}

# json_escape: JSON 문자열 안에 넣을 값을 이스케이프 처리한다.
# sed 's/\\/\\\\/g' : 역슬래시(\)를 이중 역슬래시(\\)로 변환
# sed 's/"/\\"/g'   : 큰따옴표(") 앞에 역슬래시를 추가
json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

log_action() {
  kind="$1"
  path="$2"
  printf '%s %s\n' "$kind" "$path"
}

# fail: 오류 메시지를 stderr(>&2)에 출력하고 종료 코드 1로 스크립트를 중단한다.
fail() {
  echo "$*" >&2
  exit 1
}

# ensure_source_layout: 소스 디렉터리에 필수 파일/디렉터리가 존재하는지 검증한다.
# [ -d ... ] : 디렉터리 존재 여부 검사, [ -f ... ] : 파일 존재 여부 검사
# || fail : 앞의 검사가 실패(거짓)하면 fail 함수를 실행 (OR 단락 평가)
ensure_source_layout() {
  [ -d "$SOURCE_DIR" ] || fail "source 디렉터리가 없습니다: $SOURCE_DIR"
  [ -f "$SOURCE_DIR/.claude/CLAUDE.md.example" ] || fail "source에 .claude/CLAUDE.md.example이 없습니다: $SOURCE_DIR"
  [ -d "$SOURCE_DIR/.claude/skills" ] || fail "source에 .claude/skills 디렉터리가 없습니다: $SOURCE_DIR"
}

# collect_source_paths: 소스에서 동기화할 관리 대상 파일 목록을 수집한다.
# (...) 는 서브셸을 생성하여 cd가 부모 셸의 작업 디렉터리에 영향을 주지 않도록 격리한다.
collect_source_paths() {
  (
    cd "$SOURCE_DIR"

    # 단독 파일: 존재 여부를 개별 확인 후 경로를 출력
    [ -f ".claude/CLAUDE.md.example" ] && printf '%s\n' ".claude/CLAUDE.md.example"
    [ -f ".claude/settings.json" ]     && printf '%s\n' ".claude/settings.json"

    # 디렉터리 단위 자동 수집: find로 하위의 모든 일반 파일(-type f)을 재귀 탐색
    # .claude/scripts: 설치/관리 스크립트를 제외하고 hook 스크립트만 동기화
    for dir in .claude/scripts .claude/agents .claude/docs; do
      if [ -d "$dir" ]; then
        if [ "$dir" = ".claude/scripts" ]; then
          find "$dir" -type f \
            | grep -v 'scripts/sync\.sh$' \
            | grep -v 'scripts/bootstrap\.sh$' \
            | grep -v 'scripts/promote\.sh$' \
            | grep -v 'scripts/migrate\.sh$' \
            | grep -v 'scripts/test-sync\.sh$'
        else
          find "$dir" -type f
        fi
      fi
    done

    # skills: harness-engine/ 하위 전체를 포함하되, 최상위 harness-*.md는 제외 (프로젝트 소유)
    if [ -d ".claude/skills" ]; then
      # grep -v : 일치하는 줄을 제외(-v)한다.
      # 정규식 '^\.claude/skills/harness-[^/]*\.md$':
      #   ^         : 줄의 시작
      #   [^/]*     : 슬래시가 아닌 문자 0개 이상 (즉, 하위 디렉터리가 아닌 최상위 파일만 매칭)
      #   \.md$     : .md로 끝나는 파일
      # 결과: .claude/skills/harness-xxx.md (최상위)만 제외, harness-engine/SKILL.md 등은 포함
      find ".claude/skills" -type f | grep -v '^\.claude/skills/harness-[^/]*\.md$'
    fi
  ) | sed 's#^\./##' | awk 'NF && !seen[$0]++' | LC_ALL=C sort
  # sed 's#^\./##'        : 경로 앞의 ./ 접두사를 제거한다. (# 를 구분자로 사용하여 /와 혼동 방지)
  # awk 'NF && !seen[$0]++' : NF는 빈 줄 제외, seen[] 연관배열로 중복 줄 제거 (첫 출현만 출력)
  # LC_ALL=C sort          : 로케일에 무관하게 일관된 바이트 순서로 정렬
}

# collect_source_directories: 관리 대상 파일들의 상위 디렉터리 목록을 추출한다.
collect_source_directories() {
  collect_source_paths | while IFS= read -r path; do
    # dirname: 파일 경로에서 디렉터리 부분만 추출 (예: .claude/scripts/sync.sh → .claude/scripts)
    dir=$(dirname "$path")
    if [ "$dir" != "." ]; then
      printf '%s\n' "$dir"
    fi
  done | awk '!seen[$0]++' | LC_ALL=C sort
  # awk '!seen[$0]++' : 중복 디렉터리를 제거하여 유니크한 목록만 출력
}

# manifest_entries_from_section: 매니페스트 JSON에서 특정 섹션의 배열 항목을 추출한다.
# 구/신 위치 폴백으로 매니페스트 파일 위치를 자동 탐색한다.
manifest_entries_from_section() {
  section="$1"
  manifest_path="$TARGET_DIR/$MANIFEST_FILE"

  # 신규 위치(.claude/meta/manifest.json) 없으면 구 위치(.harness-sync-manifest.json) 폴백
  if [ ! -f "$manifest_path" ]; then
    manifest_path="$TARGET_DIR/$OLD_MANIFEST_FILE"
  fi

  # [ -f ... ] || return 0 : 매니페스트 파일이 없으면 빈 결과로 정상 종료
  [ -f "$manifest_path" ] || return 0

  # awk를 사용한 간이 JSON 배열 파서:
  # -v section="$section" : 셸 변수를 awk 변수로 전달
  # $0 ~ "\"section\"" : 현재 줄에서 "section_name": 패턴을 검색하여 배열 시작 감지
  # /^[[:space:]]*\]/ : ]로 시작하는 줄이면 배열 종료
  # sub() : 줄 앞뒤의 따옴표("), 쉼표(,), 공백을 제거하여 순수 경로만 출력
  awk -v section="$section" '
    $0 ~ "\"" section "\"[[:space:]]*:" { in_section = 1; next }
    in_section && /^[[:space:]]*\]/ { in_section = 0; exit }
    in_section {
      line = $0
      sub(/^[[:space:]]*"/, "", line)
      sub(/",?[[:space:]]*$/, "", line)
      if (length(line) > 0) {
        print line
      }
    }
  ' "$manifest_path"
}

# list_contains: 줄바꿈으로 구분된 목록(haystack)에서 정확히 일치하는 항목(needle)을 검색한다.
# grep -F : 정규식이 아닌 고정 문자열로 검색 (특수문자를 리터럴로 처리)
# grep -q : 출력 없이 종료 코드만 반환 (0=발견, 1=미발견)
# grep -x : 줄 전체가 일치해야 함 (부분 일치 방지)
# -- : 이후 인자를 옵션이 아닌 검색 패턴으로 처리 (needle이 -로 시작해도 안전)
list_contains() {
  needle="$1"
  haystack="${2:-}"
  # ${2:-} : 두 번째 인자가 없거나 비어있으면 빈 문자열을 기본값으로 사용

  [ -n "$haystack" ] || return 1
  # [ -n ... ] : 문자열이 비어있지 않으면 참. 빈 목록이면 검색 불필요하므로 1(미발견) 반환
  printf '%s\n' "$haystack" | grep -Fqx -- "$needle"
}

# ensure_parent_dir: 파일을 복사하기 전 상위 디렉터리를 생성한다.
ensure_parent_dir() {
  rel_path="$1"
  # dirname: 파일 경로에서 상위 디렉터리 추출
  parent_dir=$(dirname "$rel_path")

  # "." 이면 현재 디렉터리이므로 생성 불필요
  [ "$parent_dir" = "." ] && return 0

  if [ "$DRY_RUN" -eq 1 ]; then
    return 0
  fi

  # mkdir -p : 중간 디렉터리까지 재귀적으로 생성, 이미 존재하면 무시
  mkdir -p "$TARGET_DIR/$parent_dir"
}

# set_file_mode: 소스 파일의 실행 권한을 대상 파일에 복제한다.
# [ -x "$src" ] : 소스 파일에 실행(execute) 권한이 있으면 참
# chmod 755 : 소유자 rwx(읽기/쓰기/실행), 그룹/기타 rx (실행 가능한 스크립트용)
# chmod 644 : 소유자 rw(읽기/쓰기), 그룹/기타 r(읽기만) (일반 파일용)
set_file_mode() {
  src="$1"
  dst="$2"

  if [ -x "$src" ]; then
    chmod 755 "$dst"
  else
    chmod 644 "$dst"
  fi
}

# sync_path: 단일 파일을 소스에서 대상으로 동기화한다.
# 충돌 감지: 대상에 파일이 존재하지만 이전 매니페스트에 없으면 프로젝트 소유 파일로 간주하여 건너뛴다.
# 결과를 LAST_SYNC_ACTION 전역 변수에 저장하여 호출자가 참조할 수 있게 한다.
sync_path() {
  rel_path="$1"
  src="$SOURCE_DIR/$rel_path"
  dst="$TARGET_DIR/$rel_path"
  LAST_SYNC_ACTION=""

  [ -f "$src" ] || fail "source 파일이 없습니다: $src"

  # 대상 경로가 디렉터리이면 파일로 덮어쓸 수 없으므로 오류 종료
  if [ -d "$dst" ]; then
    fail "대상 경로가 디렉터리라서 파일을 덮어쓸 수 없습니다: $dst"
  fi

  # Case 1: 대상 파일이 존재하지 않으면 새로 생성
  # [ ! -e "$dst" ] : 파일이 존재하지 않으면 참 (-e는 파일/디렉터리/심볼릭링크 모두 검사)
  if [ ! -e "$dst" ]; then
    log_action "CREATE" "$rel_path"
    if [ "$DRY_RUN" -eq 0 ]; then
      ensure_parent_dir "$rel_path"
      cp "$src" "$dst"
      set_file_mode "$src" "$dst"
    fi
    LAST_SYNC_ACTION="CREATE"
    return 0
  fi

  # Case 2: 대상 파일이 소스와 동일하면 변경 불필요
  # cmp -s : 두 파일을 바이트 단위로 비교한다. -s(silent)는 출력 없이 종료 코드만 반환.
  #          종료 코드 0이면 파일 내용이 동일함을 의미한다.
  if cmp -s "$src" "$dst"; then
    log_action "KEEP" "$rel_path"
    LAST_SYNC_ACTION="KEEP"
    return 0
  fi

  # Case 3: 대상 파일이 존재하고 내용이 다르며, 이전 매니페스트에 없는 경우
  # → 프로젝트가 자체적으로 보유한 파일이므로 덮어쓰지 않고 경고만 출력한다.
  # list_contains는 OLD_PATHS(이전 sync의 매니페스트)에서 현재 경로를 검색한다.
  if ! list_contains "$rel_path" "$OLD_PATHS"; then
    log_action "CONFLICT" "$rel_path"
    printf '  ⚠ 프로젝트에 이미 존재하는 파일입니다. 덮어쓰지 않습니다: %s\n' "$rel_path" >&2
    LAST_SYNC_ACTION="CONFLICT"
    return 0
  fi

  # Case 4: 이전 sync에서 관리하던 파일이므로 정상 업데이트
  log_action "UPDATE" "$rel_path"
  if [ "$DRY_RUN" -eq 0 ]; then
    ensure_parent_dir "$rel_path"
    cp "$src" "$dst"
    set_file_mode "$src" "$dst"
  fi
  LAST_SYNC_ACTION="UPDATE"
}

# sync_merge: 마커 기반 병합 — core 영역만 소스로 교체하고 project 영역은 보존한다.
# CLAUDE.md.example(소스) → CLAUDE.md(대상) 변환에 사용된다.
# 마커: <!-- HARNESS-SYNC-PROJECT-START -->
#   마커 이전 = core 영역 (소스에서 교체)
#   마커 이후 = project 영역 (대상에서 보존)
sync_merge() {
  src_rel_path="$1"
  dst_rel_path="$2"
  src="$SOURCE_DIR/$src_rel_path"
  dst="$TARGET_DIR/$dst_rel_path"

  [ -f "$src" ] || fail "merge source 파일이 없습니다: $src"

  if [ ! -e "$dst" ]; then
    log_action "CREATE" "$dst_rel_path"
    if [ "$DRY_RUN" -eq 0 ]; then
      ensure_parent_dir "$dst_rel_path"
      cp "$src" "$dst"
      set_file_mode "$src" "$dst"
    fi
    return 0
  fi

  # sed '/PATTERN/,$d' : PATTERN이 나타나는 줄부터 파일 끝($)까지 삭제(d)한다.
  # 결과: 마커 이전의 core 영역만 추출된다.
  core_from_template=$(sed '/HARNESS-SYNC-PROJECT-START/,$d' "$src")

  # grep -q : 패턴이 존재하는지 조용히 검사 (출력 없이 종료 코드만 반환)
  if grep -q 'HARNESS-SYNC-PROJECT-START' "$dst"; then
    # 대상에 마커가 있으면: 마커 이후의 project 영역을 추출
    # sed -n '/PATTERN/,$p' : -n은 기본 출력을 억제하고, 마커부터 끝까지만 출력(p)한다.
    project_from_target=$(sed -n '/HARNESS-SYNC-PROJECT-START/,$p' "$dst")
  else
    # 대상에 마커가 없으면: 기존 파일 전체를 project 영역으로 감싸서 보존
    project_from_target="<!-- HARNESS-SYNC-PROJECT-START -->
$(cat "$dst")"
    printf '  ℹ 기존 %s 내용을 project 영역으로 보존합니다. 마커가 삽입됩니다.\n' "$dst_rel_path" >&2
  fi

  merged="${core_from_template}
${project_from_target}"

  # printf ... | cmp -s - "$dst" : 변수 내용을 파이프로 전달하여 파일과 비교한다.
  # cmp의 - 는 표준 입력(stdin)을 의미한다. 병합 결과가 현재 파일과 동일하면 변경 불필요.
  if printf '%s\n' "$merged" | cmp -s - "$dst"; then
    log_action "KEEP" "$dst_rel_path"
    return 0
  fi

  log_action "MERGE" "$dst_rel_path"
  printf '  → core 영역 업데이트, project 영역 보존\n' >&2
  if [ "$DRY_RUN" -eq 0 ]; then
    ensure_parent_dir "$dst_rel_path"
    printf '%s\n' "$merged" > "$dst"
    set_file_mode "$src" "$dst"
  fi
}

# prune_empty_parents: 파일 삭제 후 비어있는 상위 디렉터리를 재귀적으로 정리한다.
prune_empty_parents() {
  rel_path="$1"
  dir=$(dirname "$rel_path")

  # 루트(. 또는 /)에 도달할 때까지 반복
  while [ "$dir" != "." ] && [ "$dir" != "/" ]; do
    target_dir="$TARGET_DIR/$dir"

    [ -d "$target_dir" ] || break

    # rmdir: 빈 디렉터리만 삭제한다. 내용이 있으면 실패하며, 2>/dev/null로 오류 메시지를 숨긴다.
    if ! rmdir "$target_dir" 2>/dev/null; then
      break
    fi

    dir=$(dirname "$dir")
  done
}

# remove_stale_path: 이전 sync에서 관리했지만 현재 소스에 더 이상 없는 파일을 삭제한다.
remove_stale_path() {
  rel_path="$1"
  dst="$TARGET_DIR/$rel_path"

  # [ -e "$dst" ] || return 0 : 대상 파일이 이미 없으면 아무 작업도 하지 않는다.
  [ -e "$dst" ] || return 0

  if [ -d "$dst" ]; then
    fail "manifest가 파일로 관리하던 경로가 디렉터리로 바뀌어 제거를 중단합니다: $dst"
  fi

  log_action "REMOVE" "$rel_path"

  if [ "$DRY_RUN" -eq 0 ]; then
    # rm -f : 파일을 강제 삭제한다. 파일이 없어도 오류를 발생시키지 않는다.
    rm -f "$dst"
    prune_empty_parents "$rel_path"
  fi
}

# write_manifest: 현재 동기화 상태를 JSON 매니페스트 파일에 기록한다.
# 다음 sync 실행 시 관리 대상 파일 목록과 stale 파일 감지에 사용된다.
write_manifest() {
  current_paths="$1"
  current_directories="$2"
  manifest_path="$TARGET_DIR/$MANIFEST_FILE"
  # $$ : 현재 프로세스 ID. 임시 파일 이름에 포함하여 병렬 실행 시 충돌을 방지한다.
  tmp_manifest="$manifest_path.tmp.$$"
  # git rev-parse --short HEAD : 현재 커밋의 짧은 해시를 가져온다.
  # 2>/dev/null : git 오류(예: git 저장소가 아닌 경우)를 숨긴다.
  # || printf 'unknown' : git 명령 실패 시 "unknown"을 기본값으로 사용한다.
  source_commit=$(git -C "$SOURCE_DIR" rev-parse --short HEAD 2>/dev/null || printf '%s' "unknown")

  [ "$DRY_RUN" -eq 0 ] || return 0

  mkdir -p "$(dirname "$manifest_path")"

  {
    printf '{\n'
    printf '  "format_version": 2,\n'
    printf '  "source_label": "%s",\n' "$(json_escape "$SOURCE_DIR")"
    printf '  "last_synced_commit": "%s",\n' "$(json_escape "$source_commit")"
    printf '  "managed_paths": [\n'

    first=1
    printf '%s\n' "$current_paths" | while IFS= read -r path; do
      [ -n "$path" ] || continue
      if [ "$first" -eq 1 ]; then
        first=0
        printf '    "%s"' "$(json_escape "$path")"
      else
        printf ',\n    "%s"' "$(json_escape "$path")"
      fi
    done

    printf '\n  ],\n'
    printf '  "managed_directories": [\n'

    first=1
    printf '%s\n' "$current_directories" | while IFS= read -r path; do
      [ -n "$path" ] || continue
      if [ "$first" -eq 1 ]; then
        first=0
        printf '    "%s"' "$(json_escape "$path")"
      else
        printf ',\n    "%s"' "$(json_escape "$path")"
      fi
    done

    printf '\n  ]\n'
    printf '}\n'
  } > "$tmp_manifest"

  # mv로 원자적(atomic) 교체: 쓰기 도중 중단되어도 기존 매니페스트가 손상되지 않는다.
  mv "$tmp_manifest" "$manifest_path"
  log_action "WRITE" "$MANIFEST_FILE"
}

# --- 인자 파싱 ---
# $# : 현재 남은 명령줄 인자의 개수
# case/esac : 패턴 매칭 분기문 (switch-case와 유사)
# ;; : 각 분기(case)의 종료 표시
# shift N : 처리한 인자 N개를 제거하고 나머지를 앞으로 이동한다.
# *) : 어떤 패턴에도 일치하지 않는 나머지 (default case)

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

# [ -n "$TARGET_DIR" ] : 문자열이 비어있지 않으면 참
# || { ... } : 앞 명령이 실패(거짓)하면 중괄호 블록을 실행한다 (OR 단락 평가)
[ -n "$TARGET_DIR" ] || {
  usage
  exit 1
}

# --- 메인 플로우 ---

ensure_source_layout

CURRENT_PATHS=$(collect_source_paths)
CURRENT_DIRECTORIES=$(collect_source_directories)
# OLD_PATHS: 이전 sync의 매니페스트에서 관리 대상 파일 목록을 읽어온다.
# 최초 sync 시에는 매니페스트가 없으므로 빈 문자열이 된다.
OLD_PATHS=$(manifest_entries_from_section "managed_paths")

[ -n "$CURRENT_PATHS" ] || fail "복사할 관리 대상이 없습니다."

printf 'SOURCE %s\n' "$SOURCE_DIR"
printf 'TARGET %s\n' "$TARGET_DIR"

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$TARGET_DIR"
fi

# stale-path 제거: 이전 sync에서 관리했지만 현재 소스에 더 이상 없는 파일을 정리한다.
# heredoc(<<EOF) 패턴을 사용하여 서브셸 생성을 방지한다.
# (파이프 기반 while은 서브셸에서 실행되어 전역 변수 변경이 부모 셸로 전파되지 않는다.)
while IFS= read -r old_path; do
  [ -n "$old_path" ] || continue
  if ! list_contains "$old_path" "$CURRENT_PATHS"; then
    remove_stale_path "$old_path"
  fi
done <<EOF
$(printf '%s\n' "$OLD_PATHS")
EOF

# 파일 동기화
# MANIFEST_PATHS: 실제로 동기화에 성공한 파일만 수집한다.
# CONFLICT된 파일은 매니페스트에서 제외하여 다음 sync에서도 충돌로 감지되도록 한다.
MANIFEST_PATHS=""
CONFLICT_COUNT=0

while IFS= read -r rel_path; do
  [ -n "$rel_path" ] || continue
  # CLAUDE.md.example은 마커 기반 병합(sync_merge)으로 별도 처리하므로 여기서 건너뛴다.
  # 단, 매니페스트에는 포함하여 stale 감지에 사용한다.
  if [ "$rel_path" = ".claude/CLAUDE.md.example" ]; then
    MANIFEST_PATHS="${MANIFEST_PATHS}${rel_path}
"
    continue
  fi
  sync_path "$rel_path"
  if [ "$LAST_SYNC_ACTION" = "CONFLICT" ]; then
    CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
  else
    # CONFLICT가 아닌 파일만 매니페스트 경로에 추가
    MANIFEST_PATHS="${MANIFEST_PATHS}${rel_path}
"
  fi
done <<EOF
$(printf '%s\n' "$CURRENT_PATHS")
EOF

# CLAUDE.md.example → 프로젝트 루트 CLAUDE.md 마커 기반 병합
sync_merge ".claude/CLAUDE.md.example" "CLAUDE.md"

# 매니페스트 기록: CONFLICT 파일을 제외한 실제 관리 파일만 기록
write_manifest "$MANIFEST_PATHS" "$CURRENT_DIRECTORIES"

# 구 매니페스트 정리: 이전 위치의 매니페스트 파일이 남아있으면 제거
old_manifest="$TARGET_DIR/$OLD_MANIFEST_FILE"
if [ "$DRY_RUN" -eq 0 ] && [ -f "$old_manifest" ]; then
  rm -f "$old_manifest"
  log_action "REMOVE" "$OLD_MANIFEST_FILE"
fi

# 충돌 요약: 건너뛴 파일이 있으면 사용자에게 수동 확인을 안내
if [ "$CONFLICT_COUNT" -gt 0 ]; then
  printf '\n⚠ %d개 파일이 프로젝트에 이미 존재하여 건너뛰었습니다. 수동으로 확인하세요.\n' "$CONFLICT_COUNT" >&2
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN 완료"
else
  echo "SYNC 완료"
fi
