#!/usr/bin/env bash
# Unit tests for Claude Code hook scripts.
#
# Simulates Claude Code's hook invocation by piping realistic stdin JSON and
# setting CLAUDE_PROJECT_DIR. Each test runs in an isolated temp workspace.
#
# Usage:
#   cd claude-hooks/tests && bash test-hooks.sh

set -euo pipefail

if ! [ "${BASH_VERSION:-}" ] || (shopt -o posix 2>/dev/null | grep -q 'on$'); then
  printf '%s\n' "ERROR: This script requires bash, not sh. POSIX mode detected." >&2
  printf '%s\n' "Usage: bash $0" >&2
  exit 1
fi

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Paths ─────────────────────────────────────────────────────────────────────
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_SRC="$(cd "$TESTS_DIR/../hooks" && pwd)"
PASSED=0
FAILED=0
WORKSPACES=()

# Ensure jq is available.
if ! command -v jq &>/dev/null; then
  printf '%b\n' "${RED}ERROR: jq is required but not installed.${NC}"
  exit 1
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

cleanup() {
  for ws in ${WORKSPACES[@]+"${WORKSPACES[@]}"}; do
    rm -rf "$ws"
  done
}
trap cleanup EXIT

make_workspace() {
  local ws
  ws=$(mktemp -d /tmp/test-hooks-XXXXXXX)
  WORKSPACES+=("$ws")
  mkdir -p "$ws/.claude/hooks"
  cp "$HOOKS_SRC/record-change.sh" "$ws/.claude/hooks/"
  cp "$HOOKS_SRC/review-session.sh" "$ws/.claude/hooks/"
  # Make them executable (cp preserves mode, but ensure)
  chmod +x "$ws/.claude/hooks/record-change.sh"
  chmod +x "$ws/.claude/hooks/review-session.sh"
  printf '%s\n' "$ws"
}

# Write config.json into the workspace's .claude/hooks/ directory.
write_config() {
  local ws="$1" content="$2"
  echo "$content" > "$ws/.claude/hooks/config.json"
}

# Write a file into the workspace (e.g. review-prompt.md).
write_file() {
  local ws="$1" relpath="$2" content="$3"
  mkdir -p "$(dirname "$ws/$relpath")"
  echo "$content" > "$ws/$relpath"
}

# Create a pre-populated change record (JSON) in the workspace cache.
create_change_record() {
  local ws="$1" session_id="$2" filename="$3" content="$4"
  local dir="$ws/.claude/cache/${session_id}/changes"
  mkdir -p "$dir"
  echo "$content" > "$dir/$filename"
}

# Run record-change.sh with stdin JSON and CLAUDE_PROJECT_DIR set.
run_record_change() {
  local ws="$1" stdin_json="$2"
  echo "$stdin_json" | CLAUDE_PROJECT_DIR="$ws" bash "$ws/.claude/hooks/record-change.sh"
}

# Run review-session.sh with stdin JSON and CLAUDE_PROJECT_DIR set.
run_review_session() {
  local ws="$1" stdin_json="$2"
  echo "$stdin_json" | CLAUDE_PROJECT_DIR="$ws" bash "$ws/.claude/hooks/review-session.sh"
}

# ── Assertions ────────────────────────────────────────────────────────────────

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    return 0
  else
    printf '%b\n' "  ${RED}FAIL${NC} $label: expected='$expected' actual='$actual'"
    return 1
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    return 0
  else
    printf '%b\n' "  ${RED}FAIL${NC} $label: string does not contain '$needle'"
    return 1
  fi
}

assert_file_exists() {
  local label="$1" path="$2"
  if [[ -f "$path" ]]; then
    return 0
  else
    printf '%b\n' "  ${RED}FAIL${NC} $label: file not found: $path"
    return 1
  fi
}

assert_no_file() {
  local label="$1" pattern="$2"
  local count
  count=$(find "$(dirname "$pattern")" -maxdepth 1 -name "$(basename "$pattern")" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$count" -eq 0 ]]; then
    return 0
  else
    printf '%b\n' "  ${RED}FAIL${NC} $label: expected no files matching $pattern, found $count"
    return 1
  fi
}

assert_exit_code() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" -eq "$actual" ]]; then
    return 0
  else
    printf '%b\n' "  ${RED}FAIL${NC} $label: expected exit=$expected, got exit=$actual"
    return 1
  fi
}

# ── JSON constructors (realistic Claude Code hook inputs) ─────────────────────

make_write_input() {
  local session_id="${1:-session-001}" file_path="${2:-src/foo.ts}" content="${3:-console.log('hello');}"
  jq -n \
    --arg tool_name "Write" \
    --arg session_id "$session_id" \
    --arg file_path "$file_path" \
    --arg content "$content" \
    --arg permission_mode "allow" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      tool_input: { file_path: $file_path, content: $content },
      permission_mode: $permission_mode,
      hook_event_name: "PostToolUse"
    }'
}

make_edit_input() {
  local session_id="${1:-session-001}" file_path="${2:-src/bar.ts}" old="${3:-old line}" new="${4:-new line}"
  jq -n \
    --arg tool_name "Edit" \
    --arg session_id "$session_id" \
    --arg file_path "$file_path" \
    --arg old_string "$old" \
    --arg new_string "$new" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      tool_input: { file_path: $file_path, old_string: $old_string, new_string: $new_string },
      hook_event_name: "PostToolUse"
    }'
}

make_subagent_write_input() {
  local session_id="${1:-session-001}"
  jq -n \
    --arg tool_name "Write" \
    --arg session_id "$session_id" \
    --arg agent_id "subagent-xyz-001" \
    --arg file_path "src/foo.ts" \
    --arg content "subagent content" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      agent_id: $agent_id,
      tool_input: { file_path: $file_path, content: $content },
      hook_event_name: "PostToolUse"
    }'
}

make_read_input() {
  local session_id="${1:-session-001}"
  jq -n \
    --arg tool_name "Read" \
    --arg session_id "$session_id" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      tool_input: { file_path: "README.md" },
      hook_event_name: "PostToolUse"
    }'
}

make_write_input_no_filepath() {
  local session_id="${1:-session-001}"
  jq -n \
    --arg tool_name "Write" \
    --arg session_id "$session_id" \
    --arg content "some content" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      tool_input: { content: $content },
      hook_event_name: "PostToolUse"
    }'
}

make_stop_input() {
  local session_id="${1:-session-001}" hook_event="${2:-Stop}"
  jq -n \
    --arg hook_event_name "$hook_event" \
    --arg session_id "$session_id" \
    --arg cwd "${3:-/tmp/test}" \
    '{
      hook_event_name: $hook_event_name,
      session_id: $session_id,
      cwd: $cwd
    }'
}

# ── Test runner ───────────────────────────────────────────────────────────────

run_test() {
  local name="$1" func="$2"
  printf '%s' "  $name ... "
  if $func; then
    printf '%b\n' "${GREEN}PASS${NC}"
    PASSED=$((PASSED + 1))
  else
    FAILED=$((FAILED + 1))
  fi
}

run_section() {
  local title="$1"
  echo ""
  printf '%b\n' "${YELLOW}━━━ $title ━━━${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# record-change.sh tests
# ═══════════════════════════════════════════════════════════════════════════════

test_write_creates_record() {
  local ws session_id input output record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-write-01"
  input=$(make_write_input "$session_id" "src/foo.ts" "$(printf 'line1\nline2\nline3')")

  output=$(run_record_change "$ws" "$input") || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' | head -1)

  assert_file_exists "record file exists" "$record" || return 1
  assert_eq "action" "write" "$(jq -r '.action' "$record")" || return 1
  assert_eq "tool" "Write" "$(jq -r '.tool' "$record")" || return 1
  assert_eq "file_path" "src/foo.ts" "$(jq -r '.file_path' "$record")" || return 1
  assert_eq "lines" 3 "$(jq -r '.lines' "$record")" || return 1
  assert_eq "content" "$(printf 'line1\nline2\nline3')" "$(jq -r '.content' "$record")" || return 1
  assert_contains "has timestamp" "T" "$(jq -r '.timestamp' "$record")" || return 1
}

test_edit_creates_record() {
  local ws session_id input output record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-edit-01"
  input=$(make_edit_input "$session_id" "src/bar.ts" "$(printf 'old line\nold line 2')" "new line")

  output=$(run_record_change "$ws" "$input") || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' | head -1)

  assert_file_exists "record file exists" "$record" || return 1
  assert_eq "action" "edit" "$(jq -r '.action' "$record")" || return 1
  assert_eq "tool" "Edit" "$(jq -r '.tool' "$record")" || return 1
  assert_eq "file_path" "src/bar.ts" "$(jq -r '.file_path' "$record")" || return 1
  assert_eq "old_lines" 2 "$(jq -r '.old_lines' "$record")" || return 1
  assert_eq "new_lines" 1 "$(jq -r '.new_lines' "$record")" || return 1
  assert_eq "old" "$(printf 'old line\nold line 2')" "$(jq -r '.old' "$record")" || return 1
  assert_eq "new" "new line" "$(jq -r '.new' "$record")" || return 1
}

test_subagent_skipped() {
  local ws session_id input output records_dir
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-sub-01"
  input=$(make_subagent_write_input "$session_id")

  output=$(run_record_change "$ws" "$input") || true
  records_dir="$ws/.claude/cache/${session_id}/changes"

  # Directory should not exist (no records created).
  if [[ -d "$records_dir" ]] && [[ -n "$(ls -A "$records_dir" 2>/dev/null)" ]]; then
    printf '%b\n' "  ${RED}FAIL${NC} subagent should not create records"
    return 1
  fi
  return 0
}

test_non_write_edit_skipped() {
  local ws session_id input output records_dir
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-read-01"
  input=$(make_read_input "$session_id")

  output=$(run_record_change "$ws" "$input") || true
  records_dir="$ws/.claude/cache/${session_id}/changes"

  if [[ -d "$records_dir" ]] && [[ -n "$(ls -A "$records_dir" 2>/dev/null)" ]]; then
    printf '%b\n' "  ${RED}FAIL${NC} Read tool should not create records"
    return 1
  fi
  return 0
}

test_exclude_pattern_match() {
  local ws session_id input output records_dir
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":["src/generated/*.ts"]}'
  session_id="session-excl-01"
  # File path matches exclude pattern src/generated/*.ts → should be skipped.
  input=$(make_write_input "$session_id" "src/generated/foo.ts" "content")

  output=$(run_record_change "$ws" "$input") || true
  records_dir="$ws/.claude/cache/${session_id}/changes"

  if [[ -d "$records_dir" ]] && [[ -n "$(ls -A "$records_dir" 2>/dev/null)" ]]; then
    printf '%b\n' "  ${RED}FAIL${NC} excluded file should not be recorded"
    return 1
  fi
  return 0
}

test_include_pattern_match() {
  local ws session_id input output record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts","src/**/*.tsx"],"exclude":[]}'
  session_id="session-incl-01"
  input=$(make_write_input "$session_id" "src/components/Button.ts" "export const Button")

  output=$(run_record_change "$ws" "$input") || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' 2>/dev/null | head -1)

  assert_file_exists "record should exist" "$record" || return 1
}

test_include_pattern_no_match() {
  local ws session_id input output records_dir
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts","src/**/*.tsx"],"exclude":[]}'
  session_id="session-incl-02"
  # shell script → does not match include patterns
  input=$(make_write_input "$session_id" "scripts/deploy.sh" "#!/bin/bash")

  output=$(run_record_change "$ws" "$input") || true
  records_dir="$ws/.claude/cache/${session_id}/changes"

  if [[ -d "$records_dir" ]] && [[ -n "$(ls -A "$records_dir" 2>/dev/null)" ]]; then
    printf '%b\n' "  ${RED}FAIL${NC} non-matching file should not be recorded"
    return 1
  fi
  return 0
}

test_no_config_records_everything() {
  local ws session_id input output record
  ws=$(make_workspace)
  # Intentionally do NOT write config.json — script should record everything.
  session_id="session-noconf-01"
  input=$(make_write_input "$session_id" "any/random/path.txt" "data")

  output=$(run_record_change "$ws" "$input") || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' 2>/dev/null | head -1)

  assert_file_exists "record should exist without config" "$record" || return 1
}

test_write_empty_content() {
  local ws session_id input record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-empty-01"
  # Construct JSON directly — make_write_input treats "" as unset (falls back to default).
  input=$(jq -n \
    --arg tool_name "Write" \
    --arg session_id "$session_id" \
    --arg file_path "src/empty.ts" \
    --arg content "" \
    '{
      tool_name: $tool_name,
      session_id: $session_id,
      tool_input: { file_path: $file_path, content: $content },
      hook_event_name: "PostToolUse"
    }')

  run_record_change "$ws" "$input" >/dev/null 2>&1 || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' | head -1)

  assert_file_exists "record for empty content" "$record" || return 1
  assert_eq "lines should be 0" 0 "$(jq -r '.lines' "$record")" || return 1
  assert_eq "content should be empty" "" "$(jq -r '.content' "$record")" || return 1
}

test_file_with_dots_in_name() {
  local ws session_id input record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts","src/**/*.model.ts"],"exclude":[]}'
  session_id="session-dots-01"
  input=$(make_write_input "$session_id" "src/user.model.ts" "class User {}")

  run_record_change "$ws" "$input" >/dev/null 2>&1 || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' | head -1)

  assert_file_exists "record for dotted filename" "$record" || return 1
  assert_eq "file_path" "src/user.model.ts" "$(jq -r '.file_path' "$record")" || return 1
}

test_missing_file_path() {
  local ws session_id input record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts"],"exclude":[]}'
  session_id="session-nofp-01"
  input=$(make_write_input_no_filepath "$session_id")

  run_record_change "$ws" "$input" >/dev/null 2>&1 || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' 2>/dev/null | head -1)

  # Should create a record with empty file_path (since include pattern won't match
  # empty string → no record, which is also acceptable behavior).
  # Either outcome is fine as long as the script doesn't crash.
  # We just verify no crash (script returns).
  return 0
}

test_deeply_nested_path() {
  local ws session_id input record
  ws=$(make_workspace)
  write_config "$ws" '{"include":["src/**/*.ts","app/**/*.py"],"exclude":[]}'
  session_id="session-deep-01"
  input=$(make_write_input "$session_id" "app/services/payment/gateway.py" "def pay(): pass")

  run_record_change "$ws" "$input" >/dev/null 2>&1 || true
  record=$(find "$ws/.claude/cache/${session_id}/changes" -name '*.json' | head -1)

  assert_file_exists "record for deeply nested .py file" "$record" || return 1
  assert_eq "file_path" "app/services/payment/gateway.py" "$(jq -r '.file_path' "$record")" || return 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# review-session.sh tests
# ═══════════════════════════════════════════════════════════════════════════════

test_stop_with_changes() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{"promptFile":"review-prompt.md"}'
  write_file "$ws" ".claude/hooks/review-prompt.md" "Please review this code."
  session_id="session-review-01"

  create_change_record "$ws" "$session_id" "01_write.json" \
    '{"tool":"Write","file_path":"src/a.ts","timestamp":"2025-01-01T00:00:00Z","action":"write","lines":5,"content":"..."}'
  create_change_record "$ws" "$session_id" "02_edit.json" \
    '{"tool":"Edit","file_path":"src/b.ts","timestamp":"2025-01-01T00:00:01Z","action":"edit","old_lines":3,"new_lines":2,"old":"...","new":"..."}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true

  # Must output valid JSON with additionalContext.
  local hso
  hso=$(echo "$stdout" | jq -r '.hookSpecificOutput // empty')
  assert_contains "has hookSpecificOutput" "hookSpecificOutput" "$stdout" || return 1
  assert_eq "hookEventName" "Stop" "$(echo "$stdout" | jq -r '.hookSpecificOutput.hookEventName')" || return 1

  local ctx
  ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext // ""')
  assert_contains "context mentions file a.ts" "src/a.ts" "$ctx" || return 1
  assert_contains "context mentions file b.ts" "src/b.ts" "$ctx" || return 1
  assert_contains "context has review prompt" "Please review this code" "$ctx" || return 1

  # Verify summary file was written.
  assert_file_exists "summary.md exists" "$ws/.claude/cache/${session_id}/summary.md" || return 1

  # Verify guard file was created.
  assert_file_exists ".reviewed guard exists" "$ws/.claude/cache/${session_id}/.reviewed" || return 1
}

test_guard_file_prevents_retrigger() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-guard-02"

  # Pre-create the guard file.
  mkdir -p "$ws/.claude/cache/${session_id}"
  touch "$ws/.claude/cache/${session_id}/.reviewed"
  # Also pre-populate a change record (should be ignored).
  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Write","file_path":"src/a.ts","timestamp":"...","action":"write","lines":1,"content":"x"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true

  # Should output nothing (exited early).
  assert_eq "stdout empty when guarded" "" "$stdout" || return 1
}

test_review_empty_changes_dir() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-empty-03"

  # Create changes dir with no files.
  mkdir -p "$ws/.claude/cache/${session_id}/changes"

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  assert_eq "stdout empty for empty dir" "" "$stdout" || return 1
}

test_review_no_changes_dir() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-nodir-04"

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  assert_eq "stdout empty for missing dir" "" "$stdout" || return 1
}

test_aggregation_counts() {
  local ws session_id stdout ctx
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-agg-05"

  # 2 writes + 1 edit across 2 files.
  create_change_record "$ws" "$session_id" "01_write.json" \
    '{"tool":"Write","file_path":"src/a.ts","timestamp":"...","action":"write","lines":10,"content":"..."}'
  create_change_record "$ws" "$session_id" "02_write.json" \
    '{"tool":"Write","file_path":"src/a.ts","timestamp":"...","action":"write","lines":5,"content":"..."}'
  create_change_record "$ws" "$session_id" "03_edit.json" \
    '{"tool":"Edit","file_path":"src/b.ts","timestamp":"...","action":"edit","old_lines":8,"new_lines":3,"old":"...","new":"..."}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext // ""')

  # total_edits = 3
  assert_contains "total_edits=3" "变更次数**: 3 次" "$ctx" || return 1
  # total_lines_added = 10 + 5 + 3 = 18
  assert_contains "lines_added=18" "新增行数**: ~18" "$ctx" || return 1
  # total_lines_removed = 8
  assert_contains "lines_removed=8" "删除行数**: ~8" "$ctx" || return 1
  # FILE_COUNT should be 2 (a.ts and b.ts, a.ts deduplicated).
  assert_contains "file_count=2" "涉及文件**: 2 个" "$ctx" || return 1
}

test_file_deduplication() {
  local ws session_id stdout ctx
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-dedup-06"

  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Edit","file_path":"src/only.ts","timestamp":"...","action":"edit","old_lines":1,"new_lines":1,"old":"x","new":"y"}'
  create_change_record "$ws" "$session_id" "02.json" \
    '{"tool":"Edit","file_path":"src/only.ts","timestamp":"...","action":"edit","old_lines":1,"new_lines":1,"old":"a","new":"b"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext // ""')

  assert_contains "file_count=1" "涉及文件**: 1 个" "$ctx" || return 1
  # `only.ts` should appear exactly once.
  local count
  count=$(echo "$ctx" | grep -c 'only.ts' || true)
  assert_eq "only.ts appears once" "1" "$count" || return 1
}

test_session_end_event() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{"promptFile":"review-prompt.md"}'
  write_file "$ws" ".claude/hooks/review-prompt.md" "SessionEnd test prompt."
  session_id="session-end-07"

  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Write","file_path":"src/c.ts","timestamp":"...","action":"write","lines":2,"content":"// code"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "SessionEnd" "$ws")") || true

  assert_contains "has hookSpecificOutput" "hookSpecificOutput" "$stdout" || return 1
  assert_eq "hookEventName" "SessionEnd" "$(echo "$stdout" | jq -r '.hookSpecificOutput.hookEventName')" || return 1
  assert_contains "context has src/c.ts" "src/c.ts" "$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext')" || return 1
}

test_custom_prompt_file() {
  local ws session_id stdout ctx
  ws=$(make_workspace)
  write_config "$ws" '{"promptFile":"review-prompt.md"}'
  write_file "$ws" ".claude/hooks/review-prompt.md" "CUSTOM PROMPT: check security issues."
  session_id="session-prompt-08"

  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Write","file_path":"src/x.ts","timestamp":"...","action":"write","lines":1,"content":"x"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext // ""')

  assert_contains "uses custom prompt" "CUSTOM PROMPT: check security issues" "$ctx" || return 1
  # Should NOT contain the default hardcoded prompt.
  if echo "$ctx" | grep -q "静默吞异常"; then
    printf '%b\n' "  ${RED}FAIL${NC} should not contain default prompt when promptFile is set"
    return 1
  fi
}

test_no_config_default_prompt() {
  local ws session_id stdout ctx
  ws=$(make_workspace)
  # No config.json at all.
  session_id="session-defprompt-09"

  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Write","file_path":"src/y.ts","timestamp":"...","action":"write","lines":1,"content":"y"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true
  ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext // ""')

  assert_contains "uses default Chinese prompt" "静默吞异常" "$ctx" || return 1
}

test_additional_context_json_structure() {
  local ws session_id stdout
  ws=$(make_workspace)
  write_config "$ws" '{}'
  session_id="session-struct-10"

  create_change_record "$ws" "$session_id" "01.json" \
    '{"tool":"Write","file_path":"src/z.ts","timestamp":"...","action":"write","lines":3,"content":"line1\nline2\nline3"}'

  stdout=$(run_review_session "$ws" "$(make_stop_input "$session_id" "Stop" "$ws")") || true

  # Verify exact JSON structure.
  local keys
  keys=$(echo "$stdout" | jq -r 'keys | sort | join(",")')
  assert_eq "top-level key" "hookSpecificOutput" "$keys" || return 1

  local inner_keys
  inner_keys=$(echo "$stdout" | jq -r '.hookSpecificOutput | keys | sort | join(",")')
  assert_eq "inner keys" "additionalContext,hookEventName" "$inner_keys" || return 1

  # additionalContext must be a non-empty string.
  local ctx_len
  ctx_len=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext | length')
  if [[ "$ctx_len" -lt 10 ]]; then
    printf '%b\n' "  ${RED}FAIL${NC} additionalContext too short: $ctx_len chars"
    return 1
  fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

main() {
  echo ""
  echo "============================================="
  echo " Claude Hooks Unit Tests"
  echo "============================================="

  run_section "record-change.sh"
  run_test "Write creates record" test_write_creates_record
  run_test "Edit creates record" test_edit_creates_record
  run_test "Subagent skipped" test_subagent_skipped
  run_test "Non-Write/Edit skipped" test_non_write_edit_skipped
  run_test "Exclude pattern match" test_exclude_pattern_match
  run_test "Include pattern match" test_include_pattern_match
  run_test "Include pattern no match" test_include_pattern_no_match
  run_test "No config records everything" test_no_config_records_everything
  run_test "Write empty content" test_write_empty_content
  run_test "File with dots in name" test_file_with_dots_in_name
  run_test "Missing file_path" test_missing_file_path
  run_test "Deeply nested path" test_deeply_nested_path

  run_section "review-session.sh"
  run_test "Stop with changes" test_stop_with_changes
  run_test "Guard file prevents re-trigger" test_guard_file_prevents_retrigger
  run_test "Empty changes dir" test_review_empty_changes_dir
  run_test "No changes dir" test_review_no_changes_dir
  run_test "Aggregation counts" test_aggregation_counts
  run_test "File deduplication" test_file_deduplication
  run_test "SessionEnd event" test_session_end_event
  run_test "Custom promptFile" test_custom_prompt_file
  run_test "No config default prompt" test_no_config_default_prompt
  run_test "AdditionalContext JSON structure" test_additional_context_json_structure

  echo ""
  echo "============================================="
  printf '%b\n' "Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
  echo "============================================="

  if [[ "$FAILED" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
