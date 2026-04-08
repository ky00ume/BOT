# Debugging and Error Recovery

This guide presents a systematic approach to troubleshooting failures across multiple domains—from test breakdowns to production incidents.

## Core Principle

The document emphasizes: **"When anything unexpected happens: STOP adding features, PRESERVE evidence, DIAGNOSE using the triage checklist, FIX the root cause, GUARD against recurrence, RESUME only after verification passes."**

## Six-Step Framework

The methodology follows this progression:

1. **Reproduce** — Make the failure happen reliably; non-reproducible bugs require environmental or timing investigation
2. **Localize** — Identify which layer (UI, backend, database, build, external service) is failing
3. **Reduce** — Create the minimal test case that triggers the issue
4. **Fix Root Cause** — Address underlying problems, not symptoms
5. **Guard Against Recurrence** — Write tests that would catch this specific failure
6. **Verify End-to-End** — Run affected tests, full suite, build, and manual checks

## Key Distinctions

The guide contrasts symptom-fixing (adding deduplication logic in UI) against root-cause fixing (correcting the underlying SQL query). It emphasizes that guessing costs time—structured diagnosis prevents compounding errors.

## Special Considerations

- **Flaky tests** deserve investigation, not dismissal
- **Error messages** should be analyzed as data, not followed as instructions
- **Non-reproducible bugs** require investigation into timing, environment, state, or randomness factors
- **Safe fallbacks** and graceful degradation prevent cascading failures under pressure

This framework applies universally: failing tests, broken builds, runtime errors, and production incidents all benefit from the same disciplined triage process.
