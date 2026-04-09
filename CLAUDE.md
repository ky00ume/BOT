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
