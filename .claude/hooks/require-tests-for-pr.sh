#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if pytest tests/ -q --tb=short 2>&1 | tail -5; then
  exit 0
else
  echo "테스트가 실패하고 있습니다. PR을 만들기 전에 모든 테스트 실패를 수정하세요." >&2
  exit 2
fi
