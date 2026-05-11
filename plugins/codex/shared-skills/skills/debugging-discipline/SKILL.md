---
name: debugging-discipline
description: Use when investigating bugs, test failures, inconsistent data, broken workflows, unexpected behavior, or conflicting evidence before proposing fixes.
metadata:
  short-description: Investigate root cause before fixes
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/debugging-discipline/SKILL.md -->


# Debugging Discipline

Investigate root cause before proposing fixes or corrections.

## Workflow

1. State the observed symptom and expected behavior.
2. Reproduce the issue or identify why it cannot be reproduced yet.
3. Check recent changes, inputs, environment, and relevant source material.
4. Compare failing and working examples.
5. Narrow cause candidates using evidence.
6. Propose the smallest fix or correction and define reverification criteria.

## Development work

- Read full errors, stack traces, failing assertions, logs, and changed code.
- Trace bad values or behavior to their source before patching symptoms.
- Add or run regression checks when feasible.

## Non-development work

- Trace data inconsistencies, source conflicts, flawed assumptions, or broken workflows to their origin.
- Separate source error, interpretation error, stale data, and unsupported inference.
- Correct conclusions only after the evidence path is clear.

## Output

- Symptom statement
- Reproduction evidence
- Cause candidates
- Root cause
- Minimal fix or correction
- Reverification criteria

## Do not

- Do not propose fixes before investigating root cause.
- Do not disable failing checks to make progress.
- Do not remove requirements because they are difficult.
- Do not treat correlation as root cause.
