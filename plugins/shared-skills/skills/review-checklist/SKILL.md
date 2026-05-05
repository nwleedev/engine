---
name: review-checklist
description: Use when reviewing code, plans, specs, documents, research outputs, or strategy artifacts for correctness, risk, gaps, and actionability.
metadata:
  short-description: Review artifacts for risks, gaps, and actionability
---

# Review Checklist

Review finds defects, gaps, and risks.

## Workflow

1. Identify the artifact type and the requirements it should satisfy.
2. Check whether the artifact matches the stated goal and scope.
3. Look for correctness issues, missing evidence, risk, ambiguity, and actionability gaps.
4. Order findings by severity and support each finding with evidence.
5. Separate findings, open questions, and optional improvements.

## Development work

- Prioritize correctness, security, behavior regressions, missing tests, and maintainability risks.
- Reference files, commands, or evidence precisely.
- Do not focus on style unless it affects correctness or maintainability.

## Non-development work

- Check logic, source quality, audience fit, decision usefulness, unsupported claims, and missing counterarguments.
- Distinguish factual issues from taste or preference.
- Verify that recommendations are actionable.

## Output

- Findings first
- Severity
- Evidence
- Open questions
- Suggested next action

## Do not

- Do not claim completion from review alone.
- Do not rewrite the artifact unless asked.
- Do not bury high-severity findings below summaries.
- Do not invent requirements that were not stated or implied.
