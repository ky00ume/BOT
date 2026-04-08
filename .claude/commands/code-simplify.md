# /code-simplify — Code Simplification

## Purpose
Refactor code for improved clarity without altering functionality.

## Process

1. **Understand Context** — Review existing code and its constraints (Chesterton's Fence principle)

2. **Identify Patterns** in recently changed code:
   - Deep nesting → guard clauses or extracted helpers
   - Long functions → break into focused units
   - Complex conditionals → clearer structures
   - Poor naming → meaningful variable/function names
   - Repeated patterns → consolidation opportunities
   - Unused code → removal candidates

3. **Apply Changes Incrementally** — Test after each modification to ensure behavior unchanged

4. **Verify Quality**:
   - Tests pass
   - Build succeeds
   - Changes are genuinely more understandable

## Core Principles

1. **Preserve Behavior** — Output identical for every input
2. **Follow Conventions** — Align with project patterns, not external preferences
3. **Clarity Over Cleverness** — Explicit, readable code beats compact code
4. **Maintain Balance** — Avoid over-simplification traps
5. **Scope Focused** — Touch only recently modified code unless asked

## Red Flags
- Code already clear
- You lack understanding of it
- Performance is critical
- Module will be rewritten soon

Skip simplification in these cases.

## Next Step
Use `/review` to ensure simplifications maintain code quality.
