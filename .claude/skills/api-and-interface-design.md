# API and Interface Design

This comprehensive guide covers designing stable, well-documented interfaces that are difficult to misuse.

## Key Sections

**Core Principles:**
- **Hyrum's Law**: "All observable behaviors of your system will be depended on by somebody" — treat every public behavior as a commitment
- **One-Version Rule**: Avoid forcing consumers to choose between multiple API versions
- **Contract First**: Define interfaces before implementation

**Five Core Design Rules:**

1. **Contract First** — Specify the interface as a spec before coding
2. **Consistent Error Semantics** — Use one error strategy everywhere (e.g., HTTP status codes + structured JSON)
3. **Validate at Boundaries** — Check external input at system edges; trust internal code
4. **Prefer Addition Over Modification** — Add optional fields rather than changing or removing existing ones
5. **Predictable Naming** — Use plural nouns for REST endpoints, camelCase for fields, UPPER_SNAKE for enums

## REST API Patterns

Standard resource endpoints (GET/POST/PATCH/DELETE), query parameters for filtering, pagination with metadata, and partial updates via PATCH.

## TypeScript Patterns

Discriminated unions for variants, input/output type separation, and branded types for preventing ID mix-ups.

## Red Flags & Verification

The guide identifies common anti-patterns and provides a checklist for validating API design quality.
