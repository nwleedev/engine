---
domain: prd-writing
domain_type: document
language: auto
keywords: [PRD, product, user story, acceptance criteria, feature, requirement, roadmap]
file_patterns: []
updated: 2026-04-20
---

# PRD Writing Harness

## Purpose
Define the ideal standard for product requirement documents, not the current doc state.

## Core Rules

- [ ] Every user story follows the format: "As a [user], I want [goal] so that [reason]"
- [ ] Each user story has measurable acceptance criteria (Given/When/Then or numbered list)
- [ ] Success metric is quantified — no "improve UX" without a target number
- [ ] Scope section explicitly lists what is OUT of scope
- [ ] Each requirement traces to a user problem or business goal

## Pattern Examples

### User Story

<Good>
As a first-time buyer, I want to see estimated delivery dates on the product page
so that I can plan my purchase.

Acceptance criteria:
1. Delivery estimate shows within 200ms of page load
2. Estimate reflects user's detected region
3. If unavailable, fallback text "Delivery date unavailable" is shown
</Good>

<Bad>
"The product page should show delivery info."
No actor, no goal, no acceptance criteria.
</Bad>

---

### Success Metric

<Good>
Success: checkout abandonment rate drops from 42% to below 35% within 60 days of launch.
</Good>

<Bad>
"Success: users find checkout easier."
Unmeasurable — no baseline, no target, no timeframe.
</Bad>

## Anti-Pattern Gate

```
User story missing "so that" clause?       → Add the user's goal/reason
No acceptance criteria?                     → Add Given/When/Then or numbered list
Success metric not measurable?              → Add baseline, target number, timeframe
Requirement with no problem link?           → Add "This solves: [user problem]"
```
