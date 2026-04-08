# /ship — Shipping and Launch

## Purpose
Deploy to production safely with monitoring, rollback plans, and clear success criteria.

## Pre-Launch Checklist

**1. Code Quality**
- Tests pass
- Build clean
- Linting clean
- No TODOs or console.logs
- Error handling complete

**2. Security**
- npm audit clean
- No secrets in code
- Authentication verified
- Security headers configured

**3. Performance**
- Core Web Vitals good (LCP ≤2.5s, INP ≤200ms, CLS ≤0.1)
- No N+1 queries
- Images optimized
- Bundle size acceptable

**4. Accessibility**
- Keyboard navigation works
- Screen reader compatible
- Contrast adequate (WCAG 2.1 AA)
- Loading/error/empty states handled

**5. Infrastructure**
- Environment variables set
- Migrations ready
- Monitoring configured
- Health checks in place

**6. Documentation**
- README current
- ADRs written
- Changelog updated
- API docs complete

## Deployment Process

1. **Deploy to Staging** — Verify in production-like environment
2. **Feature Flag OFF** — Ship code with feature inactive
3. **Team Testing** — Manual smoke tests
4. **5% Canary** — Gradually enable for small audience
5. **Gradual Rollout** — Increase to 100% while monitoring

## Monitoring Thresholds

- **Advance** — Error rate within 10% of baseline
- **Hold** — Error rate 10-100% above baseline
- **Rollback** — Error rate 2x baseline or higher

## Rollback Strategy

Document pre-launch with:
- Clear trigger conditions
- Step-by-step rollback procedure
- Communication plan

## Critical Warnings

- Don't skip monitoring setup
- Don't ignore feature flags
- Don't deploy Friday afternoons
- Don't proceed without rollback plan
