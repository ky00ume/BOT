# CI/CD and Automation

This comprehensive guide covers automated quality enforcement throughout the development pipeline.

## Core Purpose

The material emphasizes that "CI/CD is the enforcement mechanism for every other skill — it catches what humans and agents miss, and it does so consistently on every single change."

## Key Framework: The Quality Gate Pipeline

The document outlines an eight-stage verification process:
- Linting and code formatting
- Type checking
- Unit testing
- Build verification
- Integration testing
- End-to-end testing (optional)
- Security auditing
- Bundle size assessment

**Critical principle:** No gate can be bypassed. Rather than disabling rules when they fail, the expectation is to fix the underlying code.

## Implementation Guidance

**GitHub Actions examples** cover:
- Basic CI workflows with dependency caching
- Database integration tests using services (PostgreSQL)
- E2E testing with Playwright and artifact uploads

**Deployment strategies** include:
- Preview environments for pull requests
- Feature flags enabling safe code shipping without immediate activation
- Staged rollouts progressing from staging to production
- Reversible deployments with manual rollback workflows

## Performance Optimization

When pipelines exceed 10 minutes, recommended improvements (in order of impact):
1. Implement dependency caching
2. Parallelize independent jobs
3. Apply path-based filtering
4. Use matrix builds for test sharding
5. Optimize test suite execution
6. Consider larger runners

## Cultural Elements

The guide addresses common justifications against rigorous CI, emphasizing that "Trivial changes break builds. CI is fast for trivial changes anyway," and recommends establishing a "Build Cop" role to prevent accumulated broken states.
