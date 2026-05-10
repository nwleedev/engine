<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/requirements-clarifier/SKILL.md -->

---
name: requirements-clarifier
description: Use when a task has unclear requirements, acceptance criteria, scope, non-goals, constraints, or success conditions before planning or implementation.
metadata:
  short-description: Clarify scope, acceptance criteria, and blocking questions
---

# Requirements Clarifier

Clarify what should be done before planning, implementation, research, or production work begins.

## Workflow

1. Restate the user's goal in one or two sentences.
2. Separate scope, non-goals, constraints, and success conditions.
3. Identify all ambiguities first.
4. Classify ambiguities as blocking or non-blocking.
5. Ask only the highest-priority blocking question per assistant turn.
6. Do not hide other ambiguities. Summarize them as assumptions or pending risks.

## Development work

- Identify affected systems, likely files, dependency constraints, test expectations, and rollback concerns.
- Confirm whether the user is asking for research, planning, implementation, review, or verification.
- Stop before implementation if approval, scope, or acceptance criteria are unresolved.

## Non-development work

- Identify audience, purpose, decision owner, source requirements, format, deadline, and actionability.
- Distinguish factual research from strategy, ideation, writing, or operational planning.
- Capture assumptions that could change the recommendation or output.

## Output

- Requirement brief
- In scope
- Out of scope
- Acceptance criteria
- Blocking question
- Assumptions and pending risks

## Do not

- Do not ask a batch of unrelated questions in one turn.
- Do not proceed as if an unresolved blocking ambiguity is answered.
- Do not hide ambiguity to make the task look simpler.
- Do not start editing files or making decisions that require user approval.
