# Test-Driven Development

## Core Principle

"Write a failing test before writing the code that makes it pass." This methodology ensures code quality and serves as living documentation for expected behavior.

## The TDD Cycle

The process follows three phases:

1. **RED** — Create a test that fails, proving the feature doesn't yet exist
2. **GREEN** — Write minimal code to pass the test
3. **REFACTOR** — Improve implementation while keeping tests passing

## When to Apply TDD

Use test-driven development for:
- New feature implementation
- Bug fixes (via the Prove-It Pattern)
- Existing functionality modifications
- Edge case handling
- Any behavioral changes

Skip it for configuration adjustments, documentation, or static content without behavioral impact.

## The Prove-It Pattern for Bugs

When bugs arrive, reproduce them with failing tests first. This confirms the issue exists before attempting fixes, then proves resolution afterward.

## Test Pyramid Strategy

Structure testing effort inversely with effort cost:
- **Unit tests (~80%)**: Pure logic, milliseconds
- **Integration tests (~15%)**: Component interactions, seconds
- **E2E tests (~5%)**: Critical user flows, minutes

## Testing Best Practices

**Test State Over Interactions**: Verify outcomes, not method call sequences. Implementation-focused tests break during refactoring despite unchanged behavior.

**DAMP Over DRY**: In tests, descriptive clarity beats code reuse. Each test should tell a complete story independently.

**Real Implementations First**: Prefer actual code → fakes → stubs → mocks, in that order. Excessive mocking creates false confidence.

**Pattern**: Arrange (setup) → Act (execute) → Assert (verify)

## Browser Testing

For frontend code, combine unit tests with Chrome DevTools inspection: console errors, network responses, DOM structure, computed styles, and performance metrics.

## Key Anti-Patterns

- Testing framework code instead of application logic
- Flaky, order-dependent tests
- Poor test isolation
- Excessive mocking
- Snapshot abuse without review

The guidance emphasizes that "seems right" isn't sufficient—tests are proof.
