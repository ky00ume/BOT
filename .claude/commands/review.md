# /review — Code Review and Quality Gates

## Purpose
Evaluate code changes across five critical dimensions before merging.

## Five-Axis Framework

**1. Correctness** — Does it fulfill requirements, handle edge cases, pass meaningful tests?

**2. Readability & Simplicity** — Can engineers understand it without explanation? Clear naming, logical flow, appropriate abstraction.

**3. Architecture** — Does it align with system design, maintain clean boundaries, avoid duplication?

**4. Security** — Validates inputs, protects secrets, enforces authentication, treats external data as untrusted?

**5. Performance** — Any N+1 queries, unbounded operations, missing pagination, unnecessary synchronous calls?

## Change Sizing

- **Optimal**: ~100 lines modified
- **Acceptable**: ~300 lines if logically unified
- **Split if**: Exceeds ~1000 lines

## Review Process

1. **Understand Context** — Read intent and description first
2. **Check Tests** — Examine tests before implementation
3. **Apply Framework** — Systematically review across five axes
4. **Categorize Findings**:
   - **Critical** — Must fix before merge
   - **Important** — Should fix
   - **Nit** — Nice to improve
5. **Verify Testing** — Confirm comprehensive test coverage

## Key Requirements

- Change descriptions explain WHY, not just WHAT
- Refactoring separated from feature work
- Reviews respond within one business day
- Dead code questioned, not silently deleted

## Next Step
Use `/code-simplify` if readability improvements are needed.
