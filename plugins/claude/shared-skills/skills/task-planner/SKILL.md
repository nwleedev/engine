<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/task-planner/SKILL.md -->

---
name: task-planner
description: Use when turning approved requirements or research into a small execution plan with ordered tasks, acceptance criteria, verification, and fallback paths.
metadata:
  short-description: Create a small ordered plan with verification
---

# Task Planner

Convert approved requirements or research into a small ordered plan for one main-session task.

## Workflow

1. Confirm that requirements or research are approved enough to plan.
2. Restate scope and non-goals.
3. Break the work into ordered, atomic tasks.
4. Add acceptance criteria to each task.
5. Add verification and fallback paths.
6. Mark subagent escalation candidates without spawning subagents.

## Development work

- Name likely files, tests, commands, dependencies, and review points.
- Include failure handling for test failures, migration risk, or dependency risk.
- Keep plans small enough for one main session unless the user requests a larger plan.

## Non-development work

- Name source collection, analysis, drafting, review, and delivery steps.
- Include evidence standards and decision criteria.
- Include fallback actions if source quality or data availability is insufficient.

## Output

- Scope
- Ordered checklist
- Acceptance criteria
- Verification plan
- Fallback plan
- Subagent escalation candidates, if any

## Do not

- Do not plan unapproved implementation work.
- Do not replace Superpowers writing-plans for large implementation projects.
- Do not create vague steps such as "handle edge cases" without defining the edge cases.
- Do not spawn subagents.
