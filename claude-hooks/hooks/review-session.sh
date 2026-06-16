#!/usr/bin/env bash
# Review hook — supports two modes:
#
#   1. Stop hook (recommended): injects review prompt BEFORE Claude truly stops,
#      so Claude continues and auto-reviews. Guard file prevents infinite loop.
#   2. SessionEnd hook (fallback): writes summary for manual review next session.
#
# Configure in settings.local.json — use EITHER Stop OR SessionEnd, not both.

set -euo pipefail

INPUT=$(cat)

HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
CWD=$(echo "$INPUT" | jq -r --arg cwd "$(pwd)" '.cwd // $cwd')
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"

CACHE_DIR="${CWD}/.claude/cache/${SESSION_ID}/changes"
GUARD_FILE="${CWD}/.claude/cache/${SESSION_ID}/.reviewed"

# ── Guard: already reviewed in this session → skip ──────────────────────────
if [[ -f "$GUARD_FILE" ]]; then
  exit 0
fi

# No changes recorded → nothing to do.
if [[ ! -d "$CACHE_DIR" ]] || [[ -z "$(ls -A "$CACHE_DIR" 2>/dev/null)" ]]; then
  exit 0
fi

# ── Aggregate changes ────────────────────────────────────────────────────────
file_paths=()
total_edits=0
total_lines_added=0
total_lines_removed=0

for record in "$CACHE_DIR"/*.json; do
  [[ -f "$record" ]] || continue

  path=$(jq -r '.file_path // "?"' "$record")
  action=$(jq -r '.action // "?"' "$record")

  total_edits=$((total_edits + 1))

  if [[ "$action" == "write" ]]; then
    lines=$(jq -r '.lines // 0' "$record")
    total_lines_added=$((total_lines_added + lines))
  else
    old_l=$(jq -r '.old_lines // 0' "$record")
    new_l=$(jq -r '.new_lines // 0' "$record")
    total_lines_added=$((total_lines_added + new_l))
    total_lines_removed=$((total_lines_removed + old_l))
  fi

  # Deduplicate file paths.
  found=false
  for fp in ${file_paths[@]+"${file_paths[@]}"}; do
    if [[ "$fp" == "$path" ]]; then found=true; break; fi
  done
  if [[ "$found" == "false" ]]; then
    file_paths+=("$path")
  fi
done

FILE_COUNT=${#file_paths[@]}

# ── Build review prompt ──────────────────────────────────────────────────────
# Read from external markdown file (configured in config.json → promptFile).
REVIEW_PROMPT="请 review 本次会话的所有代码变更，重点关注：(1) 无效的 try-catch 块 (2) console.log/debugger 残留 (3) 静默吞异常导致系统看起来正常但实际不可用的问题。如果发现问题请直接在代码中修复。"
if [[ -f "$CONFIG" ]]; then
  PROMPT_FILE=$(jq -r '.promptFile // ""' "$CONFIG")
  if [[ -n "$PROMPT_FILE" && "$PROMPT_FILE" != "null" ]]; then
    PROMPT_PATH="$SCRIPT_DIR/$PROMPT_FILE"
    if [[ -f "$PROMPT_PATH" ]]; then
      REVIEW_PROMPT=$(cat "$PROMPT_PATH")
    fi
  fi
fi

FILE_LIST=""
for fp in ${file_paths[@]+"${file_paths[@]}"}; do
  FILE_LIST+="  - \`$fp\`\n"
done

SUMMARY=$(
  cat <<EOF
## 会话变更摘要

- **变更次数**: $total_edits 次
- **涉及文件**: $FILE_COUNT 个
- **新增行数**: ~$total_lines_added
- **删除行数**: ~$total_lines_removed

### 变更文件列表
$FILE_LIST
### 详细变更记录
\`.claude/cache/${SESSION_ID}/changes/\`

---
$REVIEW_PROMPT
EOF
)

# ── Write summary ────────────────────────────────────────────────────────────
SUMMARY_FILE="${CWD}/.claude/cache/${SESSION_ID}/summary.md"
mkdir -p "$(dirname "$SUMMARY_FILE")"
echo "$SUMMARY" > "$SUMMARY_FILE"

# ── Mark reviewed to prevent re-trigger ──────────────────────────────────────
# Only for Stop mode; in SessionEnd mode the session ends so no re-trigger risk.
touch "$GUARD_FILE"

# ── Output additionalContext ─────────────────────────────────────────────────
# Stop is a blocking event: additionalContext is injected BEFORE Claude's
# response is finalized, so Claude sees it and continues with the review.
# SessionEnd is non-blocking: the context is visible but not acted on.
jq -n \
  --arg summary "$SUMMARY" \
  --arg event "$HOOK_EVENT" \
  '{
    hookSpecificOutput: {
      hookEventName: $event,
      additionalContext: $summary
    }
  }'

exit 0
