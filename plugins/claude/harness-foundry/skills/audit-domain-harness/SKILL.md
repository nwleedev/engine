<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/harness-foundry/skills/audit-domain-harness/SKILL.md -->

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
5. Report findings before summaries.

Use `scripts/validate_domain_harness.py <project-root>` only as a read-only
audit aid for `docs/domain-harness/**`; it does not replace evidence-based
findings or user-approved remediation.

## Output

- Findings ordered by severity
- Evidence
- Impact
- Recommended action
- Open questions
- Residual risk

## Do not

- Do not modify files during an audit.
- Do not treat missing evidence as proof that a harness is safe.
- Do not ignore non-development risks such as source quality, privacy, brand, tone, or approval flow.
- Do not manage lab evaluation reports or sanitized evaluation cases from this plugin skill.
