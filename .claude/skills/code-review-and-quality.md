# Code Review and Quality

This document establishes a comprehensive framework for evaluating code changes across five critical dimensions before merging.

## Core Philosophy

The standard is straightforward: "Approve a change when it definitely improves overall code health, even if it isn't perfect." The goal is continuous improvement, not perfection, with recognition that flawless code doesn't exist.

## The Five Review Axes

**Correctness** examines whether code fulfills its requirements, handles edge cases properly, manages error paths, and passes meaningful tests.

**Readability & Simplicity** ensures other engineers can understand the code without explanation through clear naming, logical organization, and appropriate abstraction levels.

**Architecture** verifies the change aligns with system design, maintains clean boundaries, avoids duplication, and prevents circular dependencies.

**Security** guards against vulnerabilities by validating inputs, protecting secrets, enforcing authentication checks, and treating external data as untrusted.

**Performance** identifies bottlenecks including N+1 query patterns, unbounded operations, missing pagination, and unnecessary synchronous calls.

## Change Sizing Guidelines

Optimal changes target ~100 lines modified. Changes reaching ~300 lines remain acceptable if logically unified. Anything exceeding ~1000 lines requires splitting. The framework provides specific strategies: stacking sequential dependencies, grouping by file, creating shared code horizontally, or breaking features vertically.

## Review Process Structure

Reviewers should: understand context and intent first, examine tests before implementation, apply the five-axis framework systematically, categorize findings by severity (Critical, Important, Nit, Optional, FYI), and verify the author's testing approach.

## Key Requirements

Change descriptions must be informative enough for future readers to understand modifications without seeing diffs. Refactoring must be separated from feature work. Reviews should respond within one business day. Dead code requires explicit questioning before removal rather than silent deletion.
