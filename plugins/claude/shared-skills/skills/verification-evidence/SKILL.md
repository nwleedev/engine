<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/verification-evidence/SKILL.md -->

---
name: verification-evidence
description: Use when claiming work is complete, correct, ready, verified, or decision-ready; gather evidence, checks, remaining risks, and unverified assumptions before the claim.
metadata:
  short-description: Gather evidence before completion or readiness claims
---

# Verification Evidence

Verification gathers evidence for claims.

## Workflow

1. Identify the exact claim that needs evidence.
2. Define what would prove or disprove the claim.
3. Gather fresh command output, source evidence, checklist results, or review evidence.
4. Separate passed, failed, not-run, and not-applicable checks.
5. State remaining risks and unverified assumptions before the final claim.

## Development work

- Prefer fresh tests, lint, build, type checks, diff checks, and requirement checklists.
- Report command names and outcomes.
- If a command cannot run, explain why and mark it as not run.

## Non-development work

- Verify source coverage, citation quality, decision criteria, stakeholder constraints, and unresolved uncertainty.
- Report unsupported claims or missing sources before saying an artifact is decision-ready.
- Separate evidence from recommendation.

## Output

- Evidence summary
- Passed checks
- Failed checks
- Not-run checks
- Remaining risks
- Unverified assumptions

## Do not

- Do not claim completion without fresh evidence.
- Do not treat a review as verification unless the claim only needs review evidence.
- Do not hide failed or not-run checks.
- Do not use "should pass" language as evidence.
