---
domain: okr-planning
domain_type: document
language: auto
keywords: [OKR, objective, key result, quarterly, goal, milestone, KR, initiative]
file_patterns: []
updated: 2026-04-20
---

# OKR Planning Harness

## Purpose
Define the ideal standard for objectives and key results — outcomes, not activities.

## Core Rules

- [ ] Objectives are qualitative and inspiring — they describe a desired state, not an action
- [ ] Key Results are measurable outcomes — they answer "how will we know we succeeded?"
- [ ] Key Results are not tasks or activities ("launch X" is an initiative, not a KR)
- [ ] Each KR has a baseline and a target
- [ ] No more than 5 KRs per Objective

## Pattern Examples

### Key Result

<Good>
KR: Increase weekly active users from 12,000 to 20,000 by end of Q2.
Baseline: 12,000 WAU (April 1). Target: 20,000. Measurement: product analytics.
</Good>

<Bad>
KR: "Launch the new onboarding flow."
This is an initiative/task — it doesn't measure impact or outcome.
</Bad>

---

### Objective

<Good>
O: Become the most trusted HR tool for Korean SMBs.
(Qualitative, inspiring, describes a desired outcome state)
</Good>

<Bad>
O: "Improve the product."
Too vague — no direction, no measurable implied outcome.
</Bad>

## Anti-Pattern Gate

```
KR is a task ("launch", "build", "release")?  → Convert to outcome metric with baseline/target
KR has no baseline?                           → Add current-state number
Objective sounds like a project name?         → Rewrite as desired outcome state
More than 5 KRs per Objective?                → Reduce to the 3-5 most critical
```
