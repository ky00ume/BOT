#!/usr/bin/env bash
set -euo pipefail

cmd=$(jq -r '.tool_input.command // ""')
log_file="$(git rev-parse --show-toplevel)/.claude/command-log.txt"

printf '%s  %s\n' "$(date -Is)" "$cmd" >> "$log_file"
exit 0
