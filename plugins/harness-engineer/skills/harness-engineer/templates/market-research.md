---
domain: market-research
domain_type: document
language: auto
keywords: [market, competitor, TAM, SAM, SOM, analysis, strategy, customer, research]
file_patterns: []
updated: 2026-04-20
---

# Market Research Harness

## Purpose
This file defines the **ideal research standard**, not the current document state.

## Core Rules

- [ ] Every claim backed by source or data (include date and organization)
- [ ] Market size estimates clearly split into TAM / SAM / SOM
- [ ] Competitor comparisons use multi-dimensional matrix, not a single criterion
- [ ] Estimates include methodology (Bottom-up / Top-down)
- [ ] No unsourced assertions ("the market is large" → "TAM $X, source: Y")

## Pattern Examples

### Market Size

<Good>
TAM: Global SaaS HR market $195B (Gartner, 2025)
SAM: Domestic SMB HR SaaS $1.2B (estimated from SMBA statistics)
SOM: 3-year target 0.5% = $6M
Methodology: Top-down (global market share × domestic ratio)
</Good>

<Bad>
"The market is large and has growth potential."
No specific figures, sources, or scope breakdown
</Bad>

---

### Competitor Comparison

<Good>
| Item       | Us      | Competitor A | Competitor B |
|------------|---------|--------------|--------------|
| Price      | $29/mo  | $49/mo       | $19/mo       |
| Core feat  | AI auto | Manual entry | Basic mgmt   |
| Segment    | Startup | Enterprise   | Individual   |
</Good>

<Bad>
"We have better features than Competitor A."
Single-dimension comparison, no evidence
</Bad>

## Anti-Pattern Gate

```
Using "large/good" without figures?  → Replace with specific data
Market size without source?          → Add source, date, and organization
TAM only, no SAM/SOM?               → Specify all three levels
Single-criterion competitor compare? → Replace with multi-dimensional matrix
```
