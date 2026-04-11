---
name: failure-response
description: "Response rules for failures — errors, test failures, build failures, type errors, runtime exceptions, blocked states, and problem resolution. Use when encountering errors, test failures, or blocked states."
user-invocable: true
---

# Failure Response Rules

When errors, test failures, build failures, type errors, or runtime exceptions occur during work, first identify the **reproduction conditions and direct cause**.
Do not implement workarounds, disable functionality, reinterpret requirements, or reduce scope without resolving the direct cause.

---

## Failure Response Principles

Must perform when a problem occurs:
- Record failure symptoms
- Record reproduction steps
- Identify the direct cause or most likely cause candidates
- Compare response options per cause

Consider when comparing response options:
- Whether application goals are maintained
- Test impact
- Implementation scope impact
- Reversibility
- Whether it's a temporary response

Prohibited actions:
- Adding error-hiding handling only
- Disabling tests to make them pass
- Making failures disappear by removing features
- Marking as complete without recording the problem

Exceptions: External service outages, situations requiring immediate security blocking. Even in these cases, explicitly mark it as a temporary response and record follow-up tasks.

When leaving a temporary workaround, specify expiration conditions:
- Format: `// WORKAROUND: {problem description} — remove when {condition} is met`
- Temporary code without expiration conditions becomes permanent technical debt.

---

## Goal Immutability

Application goals and ticket goals must not be arbitrarily changed due to library/framework/tool constraints.

When library constraints are discovered, follow this order:
1. Reconfirm application goals
2. Reconfirm ticket goals
3. Evaluate whether the current implementation can achieve them
4. Investigate alternative implementations (configuration changes, different libraries, custom implementation, task splitting)

If goal changes are needed: Do not change directly — request user review.

---

## Failure Analysis Recording

Even after resolving a problem, always leave an analysis record.

Record items: symptoms, reproduction steps, direct cause/candidates, considered responses, chosen response, reason for choice.
Comparison perspectives: goal preservation, test impact, implementation complexity, reversibility.

---

## Blocked State Rules

If the direct cause is identified but cannot be resolved due to current environment/permission/external system constraints, transition to **blocked state**.

Blocked record: problem symptoms, direct cause, attempted solutions, external decisions/permissions needed, follow-up task status.
Prohibited: hiding the blocked reason and marking as complete, leaving only a temporary workaround without recording the cause.

---

## Problem Avoidance Prohibition

Actions not permitted when a problem cannot be resolved:
- Changing only the implementation approach without resolving the cause
- Removing features to make tests pass
- Marking as complete by reducing requirements
- Passing the problem to another task and marking the current task as complete

When resolution is impossible: **transition to blocked state or request user review**.
