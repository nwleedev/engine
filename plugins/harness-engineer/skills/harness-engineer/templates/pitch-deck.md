---
domain: pitch-deck
domain_type: document
language: auto
keywords: [pitch, deck, investor, startup, revenue, traction, fundraise, valuation, ARR, MRR]
file_patterns: []
updated: 2026-04-20
---

# Pitch Deck Harness

## Purpose
Define the ideal evidence standard for investor-facing pitch materials.

## Core Rules

- [ ] Every market size claim cites source and year (TAM/SAM/SOM format)
- [ ] Revenue projections state the methodology (bottom-up model preferred)
- [ ] Traction slide shows actual metrics, not relative claims ("3x growth" → "from $10K to $30K MRR")
- [ ] Team slide lists relevant past evidence, not just titles
- [ ] Competitive advantage is specific and defensible, not "better UX"

## Pattern Examples

### Market Size

<Good>
TAM: Global HR SaaS $195B (Gartner 2025)
SAM: Korean SMB HR SaaS $1.2B (estimated: SMBA 2024 SMB count × avg HR spend)
SOM: Year-3 target 0.5% = $6M ARR
</Good>

<Bad>
"The HR market is huge and growing rapidly."
No figures, no source, no segmentation.
</Bad>

---

### Revenue Projection

<Good>
Year 1: $240K ARR (20 customers × $1K/mo avg contract)
Year 2: $1.2M ARR (80 customers, 15% churn, 40% expansion revenue)
Model: Bottom-up from current pipeline conversion rate of 18%.
</Good>

<Bad>
"We project $5M ARR by Year 2."
No methodology, no assumptions, no baseline.
</Bad>

## Anti-Pattern Gate

```
Market size without TAM/SAM/SOM split?     → Add all three levels with source
Revenue projection without methodology?    → Add bottom-up model assumptions
Traction claim without absolute numbers?   → Replace "3x" with "from X to Y"
Competitive advantage is "better UX"?      → Replace with specific, defensible moat
Team title without past evidence?          → Add relevant prior achievement
```
