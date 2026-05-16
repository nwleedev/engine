---
name: claim-evidence-map
description: Use when claims, recommendations, reviews, or decisions need explicit source IDs, confidence, counterevidence, and decision impact.
metadata:
  short-description: Map claims to evidence and decisions
---

# Claim Evidence Map

## Purpose

Create a `Claim Evidence Map` so every material claim is backed by source IDs, confidence is calibrated, counterevidence is visible, and decision impact is explicit.

## Workflow

1. Assign stable claim IDs using `CLM-001`, `CLM-002`, and increasing numbers.
2. Write each claim as a single checkable statement.
3. Link each claim to one or more source IDs from `source-ledger`.
4. Set confidence as high, medium, low, or unresolved based on authority, recency, agreement, and specificity.
5. Record counterevidence, source conflicts, or missing evidence.
6. Explain how the claim affects a decision, requirement, plan, review finding, or recommendation.
7. Route closure decisions to `verification-gate` when claims support a final status.

## Development work

- Map technical claims to official docs, local code, tests, release notes, or standards.
- Record compatibility and migration risk when counterevidence shows version differences.
- Keep implementation choices reversible when confidence is medium or low.

## Non-development work

- Separate facts, interpretations, recommendations, and assumptions.
- Include counterevidence even when it does not change the decision.
- Mark unresolved claims instead of overstating confidence.

## Output

```markdown
## Claim Evidence Map

| claim_id | claim | source_ids | confidence | counterevidence | decision_impact |
| --- | --- | --- | --- | --- | --- |
| CLM-001 |  | SRC-001 |  |  |  |
```

## Do not

- Do not combine multiple claims into one claim ID.
- Do not use high confidence when evidence is stale, indirect, or conflicted.
- Do not omit counterevidence because it is inconvenient.
- Do not make recommendations from unsupported claims.
