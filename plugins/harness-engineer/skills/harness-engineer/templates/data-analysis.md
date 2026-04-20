---
domain: data-analysis
domain_type: document
language: auto
keywords: [KPI, metric, A/B test, analysis, dashboard, conversion, retention, cohort, funnel, baseline]
file_patterns: []
updated: 2026-04-20
---

# Data Analysis Harness

## Purpose
Define the ideal evidence standard for KPI reports, A/B test results, and analytical documents.

## Core Rules

- [ ] Every metric stated with baseline — no standalone "conversion rate is 3.2%"
- [ ] Correlation never stated as causation without causal mechanism
- [ ] A/B test results include: sample size, duration, p-value or confidence interval
- [ ] Segment breakdowns shown when overall metric masks behavior differences
- [ ] Recommended action tied to specific metric threshold

## Pattern Examples

### Metric Statement

<Good>
Checkout conversion: 3.2% (baseline: 2.8% last quarter, +14% change)
Sample: 42,000 sessions over 14 days. p = 0.02 (95% CI: 0.1%–0.7% absolute lift).
</Good>

<Bad>
"Conversion rate improved to 3.2%."
No baseline, no sample size, no statistical significance.
</Bad>

---

### Causal Claim

<Good>
Correlation: users who view 3+ product images convert at 5.1% vs 2.8% for 1 image.
Causal hypothesis (not confirmed): more images reduce uncertainty. Requires RCT to validate.
</Good>

<Bad>
"Users who see more images convert better, so we should add more images."
States correlation as causation, jumps to recommendation without controlled evidence.
</Bad>

## Anti-Pattern Gate

```
Metric without baseline?                   → Add previous period or benchmark
Correlation stated as causation?           → Add "correlation only — causal link unconfirmed"
A/B result without sample size or p-value? → Add statistical significance data
Recommendation without metric threshold?   → Add "when [metric] reaches [X], then [action]"
```
