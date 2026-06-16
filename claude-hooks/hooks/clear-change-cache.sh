#!/usr/bin/env bash
# UserPromptSubmit hook: clear the change cache at the start of each prompt cycle.
# This scopes change collection to a single UserPromptSubmit → Stop cycle.
# Also clears the .reviewed guard so the Stop hook can fire in the new cycle.
#
# Hook contract:
#   Stdin:  {"hook_event_name":"UserPromptSubmit","session_id":"...","cwd":"..."}
#   Stdout: (none)
#   Exit:   0 always

set -euo pipefail

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
CWD=$(echo "$INPUT" | jq -r --arg cwd "$(pwd)" '.cwd // $cwd')

CACHE_DIR="${CWD}/.claude/cache/${SESSION_ID}/changes"
GUARD_FILE="${CWD}/.claude/cache/${SESSION_ID}/.reviewed"

rm -rf "$CACHE_DIR"
rm -f "$GUARD_FILE"

exit 0
