---
name: audit-domain-harness
description: Use when reviewing existing domain-harness registry, specs, evals, scaffold plans, and project AI configuration for gaps, conflicts, and risk.
metadata:
  short-description: Audit domain harness artifacts
---

# Audit Domain Harness

## Workflow

1. Perform a read-only audit of `docs/domain-harness/index.md`, referenced specs, evals, scaffold plans, and relevant AI configuration.
2. Compare registry status with actual files and activation state.
3. Check whether development, non-development, and mixed guardrails are complete for the declared `work_type`.
4. Identify conflicts between skills, subagents, rules, hooks, MCP guidance, and project instructions.
5. Run or request `validate_domain_harness.py` output when deterministic validation is needed.
6. Classify findings as local harness issue, upstream plugin issue, runtime activation issue, non-development quality issue, or security/privacy issue.
7. Review downstream issue/report artifacts and sanitized regression cases for `privacy_sanitization_check`.
8. Report findings before summaries.

## Output

- Findings ordered by severity
- Evidence
- Impact
- Recommended action
- Open questions
- Residual risk
- Downstream report or issue follow-up
- Sanitized upstream regression candidate status
- Local vs upstream classification

## Do not

- Do not modify files during an audit.
- Do not treat missing evidence as proof that a harness is safe.
- Do not ignore non-development risks such as source quality, privacy, brand, tone, or approval flow.
- Do not recommend upstream sharing unless the case is synthetic and public-safe.
- Do not share upstream regression candidates before `privacy_sanitization_check` is complete.
