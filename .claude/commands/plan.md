# /plan — Planning and Task Breakdown

## Purpose
Break specifications into small, verifiable tasks with clear acceptance criteria and dependency ordering.

## Workflow

1. **Review Specification** — Understand requirements and constraints from SPEC.md

2. **Map Dependencies** — Identify how components relate to each other

3. **Vertical Slicing** — Organize work so each task represents a complete feature path (database through UI), not isolated technical layers

4. **Define Tasks** — For each task, specify:
   - Description of what gets built
   - Acceptance criteria (testable)
   - Verification procedures
   - Dependencies on other tasks

5. **Establish Checkpoints** — Review gates between major phases

6. **Present Plan** — Show complete task breakdown for approval

## Output Artifacts
- **tasks/plan.md** — Detailed planning document
- **tasks/todo.md** — Actionable task list

## Next Step
Use `/build` to start implementation with `/test` (TDD) for each task.
