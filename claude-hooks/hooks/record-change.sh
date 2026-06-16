#!/usr/bin/env bash
# PostToolUse hook: record every Write/Edit to .claude/cache/{session_id}/changes/
# No inline judgment — pure data collection. SessionEnd picks up the accumulated
# records and triggers a review.

set -euo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
PERMISSION_MODE=$(echo "$INPUT" | jq -r '.permission_mode // ""')

# Subagent changes should not be recorded (they're transient / internal).
if echo "$INPUT" | jq -e '.agent_id' >/dev/null 2>&1; then
  exit 0
fi

# Only Write and Edit.
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  exit 0
fi

# ── File matching ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"

match_pattern() {
  local path="$1" pattern="$2"
  # Convert glob pattern to regex: **/ → (.*/)?, * → [^/]*
  local regex
  regex=$(echo "$pattern" | sed 's/\./\\./g' | sed 's/\*\*\//__GLOBSTAR__/g' | sed 's/\*/[^\/]*/g' | sed 's/__GLOBSTAR__/\(\.\*\/\)\?/g')
  regex="^${regex}$"
  echo "$path" | grep -qE "$regex" 2>/dev/null
}

# If config exists, respect include/exclude. Otherwise record everything.
if [[ -f "$CONFIG" ]]; then
  # Check exclude first (exclude wins over include).
  if jq -e '.exclude' "$CONFIG" >/dev/null 2>&1; then
    while IFS= read -r pattern; do
      if match_pattern "$FILE_PATH" "$pattern"; then
        exit 0
      fi
    done < <(jq -r '.exclude[]' "$CONFIG")
  fi

  # Check include list.
  if jq -e '.include' "$CONFIG" >/dev/null 2>&1; then
    matched=false
    while IFS= read -r pattern; do
      if match_pattern "$FILE_PATH" "$pattern"; then
        matched=true
        break
      fi
    done < <(jq -r '.include[]' "$CONFIG")
    if [[ "$matched" == "false" ]]; then
      exit 0
    fi
  fi
fi

# ── Record the change ────────────────────────────────────────────────────────
CACHE_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/cache/${SESSION_ID}/changes"
mkdir -p "$CACHE_DIR"

# Unique filename: timestamp + random (avoids collisions on parallel writes).
TIMESTAMP=$(date -u +%Y%m%dT%H%M%S)
RANDOM_PART=$(od -A n -t d -N 2 /dev/urandom 2>/dev/null | tr -d ' ' || echo $$)
RECORD_FILE="${CACHE_DIR}/${TIMESTAMP}_${RANDOM_PART}.json"

# Build the record.
if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // ""')
  if [[ -z "$CONTENT" ]]; then
    LINE_COUNT=0
  else
    LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')
  fi
  jq -n \
    --arg tool "$TOOL_NAME" \
    --arg file_path "$FILE_PATH" \
    --arg time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg content "$CONTENT" \
    --argjson lines "$LINE_COUNT" \
    '{
      tool: $tool,
      file_path: $file_path,
      timestamp: $time,
      action: "write",
      lines: $lines,
      content: $content
    }' > "$RECORD_FILE"
else
  OLD=$(echo "$INPUT" | jq -r '.tool_input.old_string // ""')
  NEW=$(echo "$INPUT" | jq -r '.tool_input.new_string // ""')
  OLD_LINES=$(echo "$OLD" | wc -l | tr -d ' ')
  NEW_LINES=$(echo "$NEW" | wc -l | tr -d ' ')
  jq -n \
    --arg tool "$TOOL_NAME" \
    --arg file_path "$FILE_PATH" \
    --arg time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg old "$OLD" \
    --arg new "$NEW" \
    --argjson old_lines "$OLD_LINES" \
    --argjson new_lines "$NEW_LINES" \
    '{
      tool: $tool,
      file_path: $file_path,
      timestamp: $time,
      action: "edit",
      old_lines: $old_lines,
      new_lines: $new_lines,
      old: $old,
      new: $new
    }' > "$RECORD_FILE"
fi

exit 0
