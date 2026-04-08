# /test — Test-Driven Development

## Purpose
Write tests before code to ensure correctness and create living documentation.

## TDD Cycle for New Features

1. **RED** — Write a failing test that proves the feature doesn't exist
2. **GREEN** — Write minimal code to pass the test
3. **REFACTOR** — Improve code while keeping tests passing

## Prove-It Pattern for Bug Fixes

1. **Reproduce** — Create a test that fails and proves the bug exists
2. **Fix** — Apply a fix to the code
3. **Verify** — Confirm the test now passes
4. **Guard** — Run full test suite to catch regressions

## Test Pyramid Strategy

- **~80% Unit Tests** — Pure logic, milliseconds
- **~15% Integration Tests** — Component interactions, seconds  
- **~5% E2E Tests** — Critical user flows, minutes

## Testing Best Practices

- **Test State Over Interactions** — Verify outcomes, not method calls
- **DAMP Over DRY** — Clarity in tests beats code reuse
- **Real Implementations First** — Prefer actual code → fakes → stubs → mocks
- **Arrange → Act → Assert** — Clear test structure

## Browser Testing
Combine unit tests with Chrome DevTools: console errors, network responses, DOM structure, computed styles, performance.

## Key Principle
"Seems right" is never sufficient — tests are proof.
