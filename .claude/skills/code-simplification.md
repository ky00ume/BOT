# Code Simplification

This resource outlines a systematic approach to refactoring code for improved readability without altering functionality.

## Core Principles

The guide emphasizes five foundational rules:

1. **Preserve Behavior** — "Does this produce the same output for every input?" Every change must maintain identical outputs, error handling, and side effects.

2. **Follow Conventions** — Align simplifications with existing project patterns rather than imposing external preferences.

3. **Clarity Over Cleverness** — Explicit, readable code trumps compact code requiring mental effort to parse.

4. **Maintain Balance** — Avoid over-simplification traps like aggressive inlining or combining unrelated logic.

5. **Scope Focused Changes** — Concentrate on recently modified code unless explicitly asked to broaden scope.

## The Four-Step Process

- **Step 1:** Understand existing code and its constraints (Chesterton's Fence principle)
- **Step 2:** Identify specific patterns—deep nesting, long functions, poor naming, redundancy
- **Step 3:** Apply changes incrementally with testing after each modification
- **Step 4:** Verify the result is genuinely more understandable

## When to Avoid Simplification

Don't simplify if code is already clear, you lack understanding, performance is critical, or the module will be rewritten.

The guide includes language-specific examples (TypeScript, Python, React) and a verification checklist ensuring changes maintain code quality and project alignment.
