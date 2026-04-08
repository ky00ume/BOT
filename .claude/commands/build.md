# /build — Incremental Implementation

## Purpose
Build features incrementally in thin vertical slices, ensuring the system stays working at each step.

## Workflow for Each Task

1. **Review Requirements** — Examine acceptance criteria and gather relevant code context

2. **Write Failing Tests (RED)** — Define expected behavior before writing implementation code
   - Use `/test` skill for TDD guidance

3. **Implement Minimally (GREEN)** — Add only code necessary to pass tests

4. **Validate Thoroughly** — Run full test suite and build verification

5. **Commit with Clear Message** — Use conventional commits (feat, fix, refactor, test, docs)

6. **Mark Task Complete** — Update tasks/todo.md

## Key Principles

- **Vertical Slices** — Complete paths through the stack per increment
- **Keep Working** — Project stays compilable and functional after each step
- **Feature Flags** — For incomplete work, use flags to deploy safely
- **One Change per Commit** — Each commit should be independently revertable

## Debugging
If builds break, use `/debug` to diagnose and recover.

## Next Step
When all tasks complete, use `/review` for code quality gates.
