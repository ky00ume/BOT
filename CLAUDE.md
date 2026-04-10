# Claude Code Instructions

## Core Principles

- **Investigate before editing**: Always examine the codebase first. Read existing code carefully before making any changes.
- **Never modify code without reading**: Do not change code you haven't read. Always read files first using the Read tool.
- **Understand the existing implementation**: Review the surrounding code and architecture before suggesting modifications.

## Development Guidelines

- Use dedicated tools appropriately (Read for files, Grep for search, Edit for modifications, Write for new files)
- Keep changes focused and minimal - only modify what's necessary
- Preserve existing code structure and patterns unless explicitly asked to refactor
- Test changes to ensure they work correctly before committing

## Git Workflow

- Develop on the designated feature branch: `claude/update-claude-md-instructions-Btyg1`
- Write clear, descriptive commit messages
- Push changes with: `git push -u origin <branch-name>`
- Always work on the specified branch, never push to different branches without permission

## Code Quality

- Maintain the existing code style and conventions
- Avoid introducing unnecessary complexity or refactoring
- Consider security implications (prevent injection, XSS, SQL injection, etc.)
- Don't add features beyond what's requested

## Communication

- Keep responses concise and direct
- Focus on answering questions, not over-explaining
- Reference specific file locations using `file_path:line_number` format

## Graphify

이 프로젝트에서 코드베이스 분석, 아키텍처 파악, 관계 시각화 작업이 필요할 때는
반드시 `docs/graphify-usage.md`를 먼저 참조하여 적절한 명령어와 옵션을 선택한다.

- 구조 파악 필요 시: `/graphify .` 또는 `graphify query`
- 변경사항 반영: `--update` 옵션
- 두 개념 연결 추적: `graphify path`
- 출력 결과물 위치: `GRAPH_REPORT.md`, `graph.json`, `graph.html`
