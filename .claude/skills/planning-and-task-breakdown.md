# Planning and Task Breakdown

## Core Purpose
This guide teaches how to decompose work into manageable, verifiable tasks—essential when facing large projects or unclear scope.

## When to Apply
Use this approach when you have specifications requiring breakdown, tasks feel overwhelming, work can be parallelized, or scope needs communicating to stakeholders.

## Key Principles

**The Five-Step Process:**
1. Read specs in read-only mode before coding
2. Map component dependencies visually
3. Slice work vertically (complete features) rather than horizontally (all database, then all API)
4. Structure each task with description, acceptance criteria, verification, and dependencies
5. Order tasks to satisfy dependencies and create natural checkpoints

**Task Sizing Matters:**
The guide emphasizes: "If a task is L or larger, it should be broken into smaller tasks. An agent performs best on S and M tasks." Tasks under 3-5 files typically represent optimal scope.

## Critical Distinctions

**Vertical vs. Horizontal Slicing:**
Rather than building entire systems layer-by-layer, organize around complete user workflows. For example, one task delivers "user registration" (schema + API + UI together), not separate database, backend, and frontend tasks.

## Red Flags to Avoid
- Starting code without written task lists
- Tasks lacking specific acceptance criteria
- No verification procedures
- All tasks oversized
- Ignoring dependency order
- Skipping checkpoint reviews

This methodology transforms vague requirements into executable work that survives context switches and enables reliable progress.
