#!/usr/bin/env bash
set -euo pipefail

cmd=$(jq -r '.tool_input.command // ""')

dangerous_patterns=(
  "rm -rf"
  "rm -fr"
  "git reset --hard"
  "git push.*--force"
  "git push.*-f "
  "DROP TABLE"
  "DROP DATABASE"
  "truncate.*table"
  "curl.*|.*sh"
  "wget.*|.*bash"
  "chmod -R 777"
  "> /dev/sda"
)

for pattern in "${dangerous_patterns[@]}"; do
  if echo "$cmd" | grep -qiE "$pattern"; then
    echo "차단됨: '$cmd'이 위험한 패턴 '$pattern'과 일치합니다. 더 안전한 대안을 제안하세요." >&2
    exit 2
  fi
done

exit 0
