# Incremental Implementation

## Core Concept

The strategy emphasizes "thin vertical slices"—implementing one complete piece end-to-end, testing it, and committing before moving forward. As stated in the guide: "Each increment should leave the system in a working, testable state."

## When to Apply It

Use this method for:
- Changes spanning multiple files
- New features from task breakdowns
- Code refactoring work
- Any situation involving substantial code before testing

Skip it only for minimal single-file modifications.

## The Cycle

Each slice follows: Implement → Test → Verify → Commit → Next slice

This ensures the codebase remains functional throughout development.

## Slicing Approaches

**Vertical slices** build complete paths through the stack (database through UI), delivering end-to-end functionality per slice.

**Contract-first slicing** works when backend and frontend develop simultaneously by defining API specifications first.

**Risk-first slicing** tackles uncertain or dangerous elements earliest, preventing wasted effort on dependent features.

## Key Principles

The guide emphasizes simplicity, asking: "What is the simplest thing that could work?" Avoid premature abstractions—three similar code patterns justify consolidation, not earlier.

Maintain scope discipline: "Touch only what the task requires" and avoid opportunistic cleanups outside your current work.

Keep the project compilable after each increment, use feature flags for incomplete work, and ensure each change is independently revertable.

## Red Flags to Avoid

Warning signs include writing over 100 lines without testing, mixing unrelated changes, broken builds between steps, and touching files unnecessarily.
