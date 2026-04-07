#!/bin/bash
# install-hooks.sh — Install engine hooks into a target project's settings.json
#
# Identifies engine hooks by marker prefixes:
#   - command hooks: ENGINE_HOOK=1 prefix
#   - agent hooks: [engine-hook] prompt prefix
#
# Usage:
#   bash install-hooks.sh <target-settings.json> [engine-hooks-dir]
#
# Examples:
#   bash .claude/scripts/install-hooks.sh /path/to/project/.claude/settings.json
#   bash .claude/scripts/install-hooks.sh /path/to/project/.claude/settings.json .claude/hooks

set -euo pipefail

TARGET_SETTINGS="${1:?Usage: install-hooks.sh <target-settings.json> [engine-hooks-dir]}"
ENGINE_HOOKS_DIR="${2:-$(dirname "$0")/../hooks}"

# Resolve to absolute path
ENGINE_HOOKS_DIR="$(cd "$ENGINE_HOOKS_DIR" && pwd)"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required but not installed." >&2
  exit 1
fi

if [ ! -f "$TARGET_SETTINGS" ]; then
  echo "ERROR: Target settings file not found: $TARGET_SETTINGS" >&2
  exit 1
fi

hook_files=("$ENGINE_HOOKS_DIR"/*.json)
if [ ! -f "${hook_files[0]}" ]; then
  echo "ERROR: No hook files found in: $ENGINE_HOOKS_DIR" >&2
  exit 1
fi

# 1. Backup
cp "$TARGET_SETTINGS" "${TARGET_SETTINGS}.bak"
echo "Backup created: ${TARGET_SETTINGS}.bak"

# 2. Remove existing engine hooks (marker-based identification)
#    - command hooks: command starts with ENGINE_HOOK=1
#    - agent hooks: prompt starts with [engine-hook]
CLEANED=$(jq '
  .hooks //= {} |
  .hooks |= with_entries(
    .value |= map(
      .hooks |= map(select(
        ((.command // "") | test("^ENGINE_HOOK=1") | not)
        and
        ((.prompt // "") | test("^\\[engine-hook\\]") | not)
      ))
      | select(.hooks | length > 0)
    ) | select(length > 0)
  )
' "$TARGET_SETTINGS")

# 3. Merge all engine hook source files
HARNESS_HOOKS=$(jq -s 'reduce .[] as $f ({}; . * $f)' "$ENGINE_HOOKS_DIR"/*.json)

# 4. Combine cleaned settings with new engine hooks
echo "$CLEANED" | jq --argjson hh "$HARNESS_HOOKS" '
  .hooks as $existing |
  .hooks = ($hh | to_entries | reduce .[] as $e ($existing;
    .[$e.key] = ((.[$e.key] // []) + $e.value)
  ))
' > "$TARGET_SETTINGS"

# 5. Report
HOOK_COUNT=$(echo "$HARNESS_HOOKS" | jq '[.[] | .[].hooks | length] | add // 0')
echo "Installed $HOOK_COUNT engine hooks into $TARGET_SETTINGS"
echo "User hooks preserved (no ENGINE_HOOK=1 or [engine-hook] marker)."
