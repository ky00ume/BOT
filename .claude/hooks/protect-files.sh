#!/usr/bin/env bash
set -euo pipefail

file=$(jq -r '.tool_input.file_path // .tool_input.path // ""')

protected=(
  "^\.env$"
  "^\.env\..*"
  "^\.git/.*"
  "^package-lock\.json$"
  "^yarn\.lock$"
  "^.*\.pem$"
  "^.*\.key$"
  "^secrets/.*"
)

for pattern in "${protected[@]}"; do
  # 절대경로에서 프로젝트 루트 기준 상대경로 추출
  rel_file="${file#$(pwd)/}"
  if echo "$rel_file" | grep -qE "$pattern"; then
    echo "차단됨: '$file'은 보호된 파일입니다. 이 편집이 왜 필요한지 설명하세요." >&2
    exit 2
  fi
done

exit 0
