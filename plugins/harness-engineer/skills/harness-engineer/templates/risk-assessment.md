---
domain: risk-assessment
domain_type: document
language: auto
keywords: [risk, mitigation, probability, impact, contingency, threat, vulnerability, dependency]
file_patterns: []
updated: 2026-04-20
---

# Risk Assessment Harness

## Purpose
Define the ideal standard for project and product risk documentation.

## Core Rules

- [ ] Every risk has an owner (person responsible for monitoring and mitigation)
- [ ] Probability and impact rated explicitly (High/Medium/Low or 1–5 scale, consistently applied)
- [ ] Mitigation action is specific — not "monitor closely" but a concrete step with deadline
- [ ] Residual risk stated after mitigation
- [ ] External dependencies listed as risks with fallback owner

## Pattern Examples

### Risk Entry

<Good>
Risk: Third-party payment API deprecates v2 endpoint (used by checkout flow).
Probability: High (announced sunset date: 2026-09-01)
Impact: Critical (checkout blocked for all users)
Owner: Backend lead (Austin)
Mitigation: Migrate to v3 by 2026-07-15. PR #234 created, 60% complete.
Residual risk: Low (migration on track, v3 tested in staging)
</Good>

<Bad>
"Payment API might change. We should keep an eye on it."
No owner, no probability/impact rating, no specific mitigation, no deadline.
</Bad>

## Anti-Pattern Gate

```
Risk without owner?                        → Assign a named person
Mitigation is "monitor" with no action?   → Replace with specific action + deadline
No probability/impact rating?              → Add explicit rating (H/M/L or 1–5)
No residual risk after mitigation?         → Add post-mitigation risk level
External dependency not listed as risk?   → Add entry with fallback plan
```
