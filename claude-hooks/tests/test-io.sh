#!/usr/bin/env bash
# I/O contract tests for Claude Code hook scripts.
#
# Each test case shows:
#   1. The JSON input (stdin) — exactly what Claude Code passes to the hook
#   2. The expected output — what the hook script produces
#
# Usage:
#   bash claude-hooks/tests/test-io.sh

set -euo pipefail

if ! [ "${BASH_VERSION:-}" ] || (shopt -o posix 2>/dev/null | grep -q 'on$'); then
  printf '%s\n' "ERROR: This script requires bash, not sh." >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  printf '%s\n' "ERROR: jq is required but not installed." >&2
  exit 1
fi

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_SRC="$(cd "$TESTS_DIR/../hooks" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASSED=0
FAILED=0

# ── Helpers ───────────────────────────────────────────────────────────────────

setup_ws() {
  local ws
  ws=$(mktemp -d /tmp/test-io-XXXXXXX)
  mkdir -p "$ws/.claude/hooks"
  cp "$HOOKS_SRC/record-change.sh" "$ws/.claude/hooks/"
  cp "$HOOKS_SRC/review-session.sh" "$ws/.claude/hooks/"
  chmod +x "$ws/.claude/hooks/record-change.sh" "$ws/.claude/hooks/review-session.sh"
  echo "$ws"
}

teardown_ws() { rm -rf "$1"; }

run_record() {
  local ws="$1" stdin_json="$2"
  echo "$stdin_json" | CLAUDE_PROJECT_DIR="$ws" bash "$ws/.claude/hooks/record-change.sh" 2>/dev/null
}

run_review() {
  local ws="$1" stdin_json="$2"
  echo "$stdin_json" | CLAUDE_PROJECT_DIR="$ws" bash "$ws/.claude/hooks/review-session.sh" 2>/dev/null
}

assert_pass() {
  printf '  %bPASS%b %s\n' "$GREEN" "$NC" "$1"
  PASSED=$((PASSED + 1))
}

assert_fail() {
  printf '  %bFAIL%b %s\n' "$RED" "$NC" "$1"
  FAILED=$((FAILED + 1))
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: record-change.sh — Write
# ═══════════════════════════════════════════════════════════════════════════════
test_write_io() {
  local ws record
  ws=$(setup_ws)
  echo '{"include":["src/**/*.ts"],"exclude":[]}' > "$ws/.claude/hooks/config.json"

  # ── INPUT (stdin JSON from Claude Code PostToolUse hook) ──────────────────
  local input
  input=$(jq -n '{
    tool_name: "Write",
    session_id: "io-test-write",
    tool_input: {
      file_path: "src/index.ts",
      content: "export const x = 1;\nexport const y = 2;\n"
    },
    permission_mode: "allow",
    hook_event_name: "PostToolUse"
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  run_record "$ws" "$input"
  record=$(find "$ws/.claude/cache/io-test-write/changes" -name '*.json' 2>/dev/null | head -1)

  # ── OUTPUT (record file written to disk) ─────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT (record file) ──${NC}"
  if [[ -z "$record" ]]; then
    echo "  (no record created)"
    assert_fail "Write: no record file created"
  else
    cat "$record" | jq .
    echo ""

    # Verify the output contract.
    local action lines file_path
    action=$(jq -r '.action' "$record")
    lines=$(jq -r '.lines' "$record")
    file_path=$(jq -r '.file_path' "$record")

    if [[ "$action" == "write" && "$lines" == "2" && "$file_path" == "src/index.ts" ]]; then
      assert_pass "Write: action=write, lines=2, file_path=src/index.ts"
    else
      assert_fail "Write: expected action=write lines=2 file_path=src/index.ts, got action=$action lines=$lines file_path=$file_path"
    fi
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: record-change.sh — Edit
# ═══════════════════════════════════════════════════════════════════════════════
test_edit_io() {
  local ws record
  ws=$(setup_ws)
  echo '{"include":["src/**/*.ts"],"exclude":[]}' > "$ws/.claude/hooks/config.json"

  # ── INPUT ────────────────────────────────────────────────────────────────
  local input
  input=$(jq -n '{
    tool_name: "Edit",
    session_id: "io-test-edit",
    tool_input: {
      file_path: "src/utils.ts",
      old_string: "function old() {\n  return 1;\n}",
      new_string: "function new() {\n  return 2;\n}"
    },
    hook_event_name: "PostToolUse"
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  run_record "$ws" "$input"
  record=$(find "$ws/.claude/cache/io-test-edit/changes" -name '*.json' 2>/dev/null | head -1)

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT (record file) ──${NC}"
  if [[ -z "$record" ]]; then
    echo "  (no record created)"
    assert_fail "Edit: no record file created"
  else
    cat "$record" | jq .
    echo ""

    local action old_lines new_lines file_path
    action=$(jq -r '.action' "$record")
    old_lines=$(jq -r '.old_lines' "$record")
    new_lines=$(jq -r '.new_lines' "$record")
    file_path=$(jq -r '.file_path' "$record")

    if [[ "$action" == "edit" && "$old_lines" == "3" && "$new_lines" == "3" && "$file_path" == "src/utils.ts" ]]; then
      assert_pass "Edit: action=edit, old_lines=3, new_lines=3, file_path=src/utils.ts"
    else
      assert_fail "Edit: expected action=edit old_lines=3 new_lines=3, got action=$action old=$old_lines new=$new_lines"
    fi
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: record-change.sh — Subagent skip (agent_id present → no record)
# ═══════════════════════════════════════════════════════════════════════════════
test_subagent_skip_io() {
  local ws
  ws=$(setup_ws)
  echo '{"include":["src/**/*.ts"],"exclude":[]}' > "$ws/.claude/hooks/config.json"

  # ── INPUT (has agent_id → should be skipped) ─────────────────────────────
  local input
  input=$(jq -n '{
    tool_name: "Write",
    session_id: "io-test-sub",
    agent_id: "subagent-abc-123",
    tool_input: {
      file_path: "src/foo.ts",
      content: "subagent work"
    },
    hook_event_name: "PostToolUse"
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  run_record "$ws" "$input"

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT ──${NC}"
  if [[ -d "$ws/.claude/cache/io-test-sub/changes" ]] && [[ -n "$(ls -A "$ws/.claude/cache/io-test-sub/changes" 2>/dev/null)" ]]; then
    echo "  (record was created — BAD)"
    assert_fail "Subagent: record should NOT be created when agent_id is present"
  else
    echo "  (no record — correct: subagent calls are skipped)"
    assert_pass "Subagent: no record (correctly skipped)"
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: record-change.sh — File excluded by glob pattern
# ═══════════════════════════════════════════════════════════════════════════════
test_exclude_io() {
  local ws
  ws=$(setup_ws)
  echo '{"include":["src/**/*.ts"],"exclude":["src/generated/*.ts"]}' > "$ws/.claude/hooks/config.json"

  # ── INPUT ────────────────────────────────────────────────────────────────
  local input
  input=$(jq -n '{
    tool_name: "Write",
    session_id: "io-test-excl",
    tool_input: {
      file_path: "src/generated/auto.ts",
      content: "// auto-generated, do not edit"
    },
    hook_event_name: "PostToolUse"
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .
  printf '%b\n' "${CYAN}── Config exclude ──${NC}"
  printf '  %s\n' '["src/generated/*.ts"]'

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  run_record "$ws" "$input"

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT ──${NC}"
  if [[ -d "$ws/.claude/cache/io-test-excl/changes" ]] && [[ -n "$(ls -A "$ws/.claude/cache/io-test-excl/changes" 2>/dev/null)" ]]; then
    echo "  (record was created — BAD)"
    assert_fail "Exclude: record should NOT be created for excluded path"
  else
    echo "  (no record — correctly filtered by exclude pattern)"
    assert_pass "Exclude: no record (correctly filtered)"
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: review-session.sh — Stop event with change records
# ═══════════════════════════════════════════════════════════════════════════════
test_stop_review_io() {
  local ws stdout
  ws=$(setup_ws)
  echo '{"promptFile":"review-prompt.md"}' > "$ws/.claude/hooks/config.json"
  printf '%s\n' "Please review for security issues and debugger statements." > "$ws/.claude/hooks/review-prompt.md"

  local sid="io-test-stop"

  # Pre-populate change records (simulating prior PostToolUse hooks).
  mkdir -p "$ws/.claude/cache/${sid}/changes"
  jq -n '{
    tool: "Write", file_path: "src/login.ts", timestamp: "2026-06-16T10:00:00Z",
    action: "write", lines: 15,
    content: "export function login() {\n  console.log(\"DEBUG\");\n  return true;\n}"
  }' > "$ws/.claude/cache/${sid}/changes/01_write.json"

  jq -n '{
    tool: "Edit", file_path: "src/auth.ts", timestamp: "2026-06-16T10:01:00Z",
    action: "edit", old_lines: 5, new_lines: 3,
    old: "try {\n  await validate();\n} catch(e) {\n}",
    new: "await validate();"
  }' > "$ws/.claude/cache/${sid}/changes/02_edit.json"

  # ── INPUT (stdin JSON from Claude Code Stop hook) ────────────────────────
  local input
  input=$(jq -n --arg cwd "$ws" '{
    hook_event_name: "Stop",
    session_id: "io-test-stop",
    cwd: $cwd
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .
  printf '%b\n' "${CYAN}── Pre-existing records ──${NC}"
  printf '  2 records in .claude/cache/io-test-stop/changes/\n'

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  stdout=$(run_review "$ws" "$input")

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT (stdout JSON) ──${NC}"
  if [[ -z "$stdout" ]]; then
    echo "  (no output — BAD)"
    assert_fail "Stop review: expected additionalContext output, got nothing"
  else
    echo "$stdout" | jq .
    echo ""

    # Verify output contract.
    local event ctx
    event=$(echo "$stdout" | jq -r '.hookSpecificOutput.hookEventName')
    ctx=$(echo "$stdout" | jq -r '.hookSpecificOutput.additionalContext')

    local ok=true
    if [[ "$event" != "Stop" ]]; then
      assert_fail "Stop review: hookEventName=$event (expected Stop)"
      ok=false
    fi
    if ! echo "$ctx" | grep -q 'src/login.ts'; then
      assert_fail "Stop review: additionalContext missing src/login.ts"
      ok=false
    fi
    if ! echo "$ctx" | grep -q 'src/auth.ts'; then
      assert_fail "Stop review: additionalContext missing src/auth.ts"
      ok=false
    fi
    if ! echo "$ctx" | grep -q '变更次数.*2'; then
      assert_fail "Stop review: additionalContext missing change count"
      ok=false
    fi
    if ! echo "$ctx" | grep -q 'Please review for security'; then
      assert_fail "Stop review: additionalContext missing custom prompt"
      ok=false
    fi

    $ok && assert_pass "Stop review: valid additionalContext with 2 files, custom prompt"

    # Verify side effects.
    if [[ -f "$ws/.claude/cache/${sid}/summary.md" ]]; then
      assert_pass "Stop review: summary.md written"
    else
      assert_fail "Stop review: summary.md NOT written"
    fi
    if [[ -f "$ws/.claude/cache/${sid}/.reviewed" ]]; then
      assert_pass "Stop review: .reviewed guard file created"
    else
      assert_fail "Stop review: .reviewed guard NOT created"
    fi
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: review-session.sh — Guard file prevents re-trigger
# ═══════════════════════════════════════════════════════════════════════════════
test_guard_io() {
  local ws stdout
  ws=$(setup_ws)
  echo '{}' > "$ws/.claude/hooks/config.json"

  local sid="io-test-guard"
  mkdir -p "$ws/.claude/cache/${sid}/changes"
  echo '{"tool":"Write","file_path":"src/x.ts","action":"write","lines":1,"content":"x"}' \
    > "$ws/.claude/cache/${sid}/changes/01.json"

  # Pre-create the guard file — simulates a prior Stop hook run.
  touch "$ws/.claude/cache/${sid}/.reviewed"

  # ── INPUT ────────────────────────────────────────────────────────────────
  local input
  input=$(jq -n --arg cwd "$ws" '{
    hook_event_name: "Stop",
    session_id: "io-test-guard",
    cwd: $cwd
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .
  printf '%b\n' "${CYAN}── Pre-existing guard ──${NC}"
  printf '  .claude/cache/io-test-guard/.reviewed exists\n'

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  stdout=$(run_review "$ws" "$input")

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT ──${NC}"
  if [[ -z "$stdout" ]]; then
    echo "  (empty — correct: guard file prevents re-trigger)"
    assert_pass "Guard: no output (correctly suppressed by .reviewed)"
  else
    echo "$stdout" | jq .
    assert_fail "Guard: expected empty output, got JSON"
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Test: review-session.sh — No records (empty → skip)
# ═══════════════════════════════════════════════════════════════════════════════
test_empty_review_io() {
  local ws stdout
  ws=$(setup_ws)
  echo '{}' > "$ws/.claude/hooks/config.json"

  # ── INPUT ────────────────────────────────────────────────────────────────
  local input
  input=$(jq -n --arg cwd "$ws" '{
    hook_event_name: "Stop",
    session_id: "io-test-empty",
    cwd: $cwd
  }')

  printf '%b\n' "${CYAN}── INPUT ──${NC}"
  echo "$input" | jq .
  printf '%b\n' "${CYAN}── Pre-existing records ──${NC}"
  printf '  (none — no changes directory)\n'

  # ── EXECUTE ──────────────────────────────────────────────────────────────
  stdout=$(run_review "$ws" "$input")

  # ── OUTPUT ──────────────────────────────────────────────────────────────
  printf '%b\n' "${CYAN}── OUTPUT ──${NC}"
  if [[ -z "$stdout" ]]; then
    echo "  (empty — correct: nothing to review)"
    assert_pass "Empty: no output (no records to review)"
  else
    echo "$stdout" | jq .
    assert_fail "Empty: expected empty output when no changes"
  fi

  teardown_ws "$ws"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

main() {
  printf '\n=============================================\n'
  printf ' Claude Hooks I/O Contract Tests\n'
  printf '=============================================\n'

  printf '\n%b━━━ record-change.sh ━━━%b\n' "$YELLOW" "$NC"
  test_write_io
  test_edit_io
  test_subagent_skip_io
  test_exclude_io

  printf '\n%b━━━ review-session.sh ━━━%b\n' "$YELLOW" "$NC"
  test_stop_review_io
  test_guard_io
  test_empty_review_io

  printf '\n=============================================\n'
  printf 'Results: %b%d passed%b, %b%d failed%b\n' \
    "$GREEN" "$PASSED" "$NC" "$RED" "$FAILED" "$NC"
  printf '=============================================\n'

  [[ "$FAILED" -eq 0 ]] && exit 0 || exit 1
}

main "$@"
