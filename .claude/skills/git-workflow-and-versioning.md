# Git Workflow and Versioning

This guide establishes disciplined version control practices for AI-assisted development.

## Core Strategy

The document strongly advocates **trunk-based development**: maintaining a constantly deployable `main` branch with short-lived feature branches (1-3 days). As stated: "Long-lived development branches are hidden costs — they diverge, create merge conflicts, and delay integration."

## Essential Practices

**Atomic Commits**: Each commit should accomplish one logical task. The guidance explains that "commits are save points" — if the next change breaks something, you can instantly revert to the last working state.

**Descriptive Messages**: Commit messages should explain *why* a change exists, not just *what* changed. Use conventional format (feat, fix, refactor, test, docs, chore) with optional body text clarifying intent.

**Size Discipline**: Target approximately 100 lines per commit, with 300 lines acceptable for single logical changes. Anything exceeding 1000 lines should be split before submission.

**Separation of Concerns**: Keep refactoring distinct from feature work. These represent fundamentally different types of changes requiring separate commits and reviews.

## Practical Tools

The guide recommends git worktrees for parallel agent work, allowing multiple features to develop simultaneously in separate directories without branch-switching overhead.

## Change Documentation

After modifications, provide structured summaries including what changed, what was intentionally excluded, and potential concerns — demonstrating scope discipline and catching assumptions early.
