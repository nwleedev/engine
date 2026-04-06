#!/bin/bash
# test-sync.sh — sync.sh 스모크 테스트
# sync의 핵심 동작(파일 복사, 멱등성, stale 제거, 매니페스트, 제외 필터)을 자동 검증한다.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
SYNC_SH="$SCRIPT_DIR/sync.sh"
TMP_DIR=""
PASSED=0
FAILED=0

# --- 유틸리티 ---

setup() {
  TMP_DIR=$(mktemp -d)
  mkdir -p "$TMP_DIR"
}

teardown() {
  [ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR"
}

assert_file_exists() {
  if [ -f "$1" ]; then
    return 0
  else
    echo "    FAIL: 파일 없음 — $1"
    return 1
  fi
}

assert_file_not_exists() {
  if [ ! -e "$1" ]; then
    return 0
  else
    echo "    FAIL: 파일 존재 — $1"
    return 1
  fi
}

assert_output_contains() {
  local output="$1"
  local pattern="$2"
  if echo "$output" | grep -q "$pattern"; then
    return 0
  else
    echo "    FAIL: 출력에 '$pattern' 없음"
    return 1
  fi
}

assert_output_not_contains() {
  local output="$1"
  local pattern="$2"
  if ! echo "$output" | grep -q "$pattern"; then
    return 0
  else
    echo "    FAIL: 출력에 '$pattern' 있음 (없어야 함)"
    return 1
  fi
}

run_test() {
  local name="$1"

  printf '  [TEST] %s ... ' "$name"
  if "$2"; then
    printf 'PASS\n'
    PASSED=$((PASSED + 1))
  else
    printf 'FAIL\n'
    FAILED=$((FAILED + 1))
  fi
  # 테스트 성공/실패 관계없이 임시 디렉터리 정리
  teardown
}

# --- 테스트 케이스 ---

test_fresh_sync() {
  setup
  local target="$TMP_DIR/fresh"
  mkdir -p "$target"

  bash "$SYNC_SH" --target "$target" > /dev/null 2>&1

  # 핵심 파일 존재 확인
  assert_file_exists "$target/.claude/settings.json" || return 1
  assert_file_exists "$target/.claude/scripts/sync.sh" || return 1
  assert_file_exists "$target/.claude/skills/core-rules.md" || return 1
  assert_file_exists "$target/.claude/skills/harness-engine/SKILL.md" || return 1
  assert_file_exists "$target/.claude/agents/work-reviewer/AGENT.md" || return 1
  assert_file_exists "$target/.claude/agents/plan-readiness-checker/AGENT.md" || return 1
  assert_file_exists "$target/.claude/docs/GETTING-STARTED.md" || return 1
  assert_file_exists "$target/CLAUDE.md" || return 1
  # 매니페스트 생성 확인
  assert_file_exists "$target/.claude/meta/manifest.json" || return 1
}

test_idempotency() {
  setup
  local target="$TMP_DIR/idempotent"
  mkdir -p "$target"

  bash "$SYNC_SH" --target "$target" > /dev/null 2>&1
  local output
  output=$(bash "$SYNC_SH" --target "$target" 2>&1)

  # 두 번째 실행: 모든 파일이 KEEP이어야 함
  assert_output_not_contains "$output" "^CREATE " || return 1
  assert_output_not_contains "$output" "^UPDATE " || return 1
  assert_output_contains "$output" "KEEP" || return 1
}

test_stale_path_removal() {
  setup
  local target="$TMP_DIR/stale"
  mkdir -p "$target"

  bash "$SYNC_SH" --target "$target" > /dev/null 2>&1

  # 매니페스트에 가짜 항목 주입 + 파일 생성
  local manifest="$target/.claude/meta/manifest.json"
  jq '.managed_paths += [".claude/scripts/stale-test.sh"]' "$manifest" > "$manifest.tmp"
  mv "$manifest.tmp" "$manifest"
  echo "stale" > "$target/.claude/scripts/stale-test.sh"

  local output
  output=$(bash "$SYNC_SH" --target "$target" 2>&1)

  assert_output_contains "$output" "REMOVE .claude/scripts/stale-test.sh" || return 1
  assert_file_not_exists "$target/.claude/scripts/stale-test.sh" || return 1
}

test_old_manifest_migration() {
  setup
  local target="$TMP_DIR/migrate"
  mkdir -p "$target"

  # 초기 sync
  bash "$SYNC_SH" --target "$target" > /dev/null 2>&1

  # 매니페스트를 구 위치로 이동
  mv "$target/.claude/meta/manifest.json" "$target/.harness-sync-manifest.json"
  rmdir "$target/.claude/meta" 2>/dev/null || true

  # 재sync
  local output
  output=$(bash "$SYNC_SH" --target "$target" 2>&1)

  # 신 위치 생성, 구 위치 제거 확인
  assert_file_exists "$target/.claude/meta/manifest.json" || return 1
  assert_file_not_exists "$target/.harness-sync-manifest.json" || return 1
  assert_output_contains "$output" "REMOVE .harness-sync-manifest.json" || return 1
}

test_harness_skill_exclusion() {
  setup
  local target="$TMP_DIR/exclude"
  mkdir -p "$target"

  # 소스에 가짜 하네스 생성
  local fake_harness="$SOURCE_DIR/.claude/skills/harness-test-fake.md"
  echo "fake" > "$fake_harness"

  local output
  output=$(bash "$SYNC_SH" --dry-run --target "$target" 2>&1)

  # 정리 (테스트 실패해도 반드시 제거)
  rm -f "$fake_harness"

  # harness-test-fake.md가 출력에 없어야 함
  assert_output_not_contains "$output" "harness-test-fake" || return 1
  # harness-engine 내 파일은 여전히 포함
  assert_output_contains "$output" "harness-engine/SKILL.md" || return 1
}

test_dry_run_no_side_effects() {
  setup
  local target="$TMP_DIR/dryrun"
  mkdir -p "$target"

  bash "$SYNC_SH" --dry-run --target "$target" > /dev/null 2>&1

  # dry-run 후 타겟에 파일이 없어야 함
  assert_file_not_exists "$target/.claude/settings.json" || return 1
  assert_file_not_exists "$target/.claude/meta/manifest.json" || return 1
  assert_file_not_exists "$target/CLAUDE.md" || return 1
}

test_manifest_format() {
  setup
  local target="$TMP_DIR/format"
  mkdir -p "$target"

  bash "$SYNC_SH" --target "$target" > /dev/null 2>&1

  local manifest="$target/.claude/meta/manifest.json"

  # JSON 유효성 검증
  if ! jq empty "$manifest" 2>/dev/null; then
    echo "    FAIL: 유효하지 않은 JSON"
    return 1
  fi

  # format_version 확인
  local version
  version=$(jq -r '.format_version' "$manifest")
  if [ "$version" != "2" ]; then
    echo "    FAIL: format_version=$version (expected 2)"
    return 1
  fi

  # managed_paths에 settings.json 포함 확인
  if ! jq -e '.managed_paths[] | select(. == ".claude/settings.json")' "$manifest" > /dev/null 2>&1; then
    echo "    FAIL: managed_paths에 .claude/settings.json 없음"
    return 1
  fi
}

# --- 실행 ---

echo "=== sync.sh 스모크 테스트 ==="
echo ""

run_test "빈 타겟에 sync" test_fresh_sync
run_test "재sync 멱등성" test_idempotency
run_test "stale-path 제거" test_stale_path_removal
run_test "구 매니페스트 마이그레이션" test_old_manifest_migration
run_test "harness-*.md 제외" test_harness_skill_exclusion
run_test "dry-run 부작용 없음" test_dry_run_no_side_effects
run_test "매니페스트 JSON 유효성" test_manifest_format

echo ""
echo "=== 결과: ${PASSED} passed, ${FAILED} failed ==="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
