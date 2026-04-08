# Performance Optimization

## Core Philosophy
"Measure before optimizing. Performance work without measurement is guessing" — the guide emphasizes profiling first to identify actual bottlenecks rather than assuming where problems exist.

## Key Workflow
The optimization process follows five steps:
1. **Measure** — Establish baseline metrics
2. **Identify** — Pinpoint the actual bottleneck
3. **Fix** — Address the specific issue
4. **Verify** — Confirm improvements with new measurements
5. **Guard** — Prevent future regressions

## Core Web Vitals Targets
- **LCP** (Largest Contentful Paint): ≤ 2.5s for "Good"
- **INP** (Interaction to Next Paint): ≤ 200ms for "Good"
- **CLS** (Cumulative Layout Shift): ≤ 0.1 for "Good"

## Common Bottlenecks & Solutions

**Frontend issues:**
- N+1 queries → Use database joins/includes
- Large bundles → Implement code splitting
- Unoptimized images → Use responsive sizing, lazy loading
- Unnecessary re-renders → Stabilize references, use React.memo strategically

**Backend issues:**
- Slow queries → Add indexes, avoid N+1 patterns
- Memory leaks → Implement caching with TTL
- Missing pagination → Enforce limits on list endpoints

## Critical Red Flags
The guide warns against optimizing without measurement data, overusing performance tools like `useMemo`, and ignoring production monitoring. Bundle size growth, unindexed queries, and images lacking dimensions are specific anti-patterns to avoid.
