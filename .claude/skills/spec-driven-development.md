# Spec-Driven Development

## Core Concept

The methodology treats the spec as "the shared source of truth between you and the human engineer — it defines what we're building, why, and how we'll know it's done."

## When to Apply

Use spec-driven development for:
- New projects or features
- Ambiguous or incomplete requirements
- Multi-file changes
- Architectural decisions
- Tasks exceeding 30 minutes

Skip it for single-line fixes or unambiguous, self-contained changes.

## Four-Phase Workflow

**Phase 1: Specify** — Create a comprehensive specification covering six areas: objective, commands, project structure, code style, testing strategy, and boundaries. Surface assumptions immediately before proceeding.

**Phase 2: Plan** — Develop a technical implementation strategy identifying components, dependencies, implementation order, risks, and verification checkpoints.

**Phase 3: Tasks** — Decompose the plan into discrete, completable units with acceptance criteria and verification steps.

**Phase 4: Implement** — Execute tasks incrementally following test-driven development practices.

## Key Principles

- The spec is a living document requiring updates as decisions or scope change
- Success criteria should be specific and measurable, not vague
- Commit specifications to version control alongside code
- A 15-minute specification typically prevents hours of rework

## Red Flags

Avoid starting development without written requirements or proceeding when success criteria remain undefined.
