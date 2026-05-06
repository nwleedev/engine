# Harness Change Review

## Summary

- Domain:
- Work type:
- Change type:

## Checks

- [ ] `docs/domain-harness/index.md` remains the source of truth.
- [ ] `spec.md`, `evals.md`, and `scaffold.md` references are valid.
- [ ] AGENTS.md, MCP, hooks, and subagents were not modified or activated without explicit approval.
- [ ] `privacy_sanitization_check` was completed for reports or upstream regression cases.
- [ ] Validator output is attached or summarized.

## Verification

```bash
rtk python3 plugins/harness-foundry/scripts/validate_domain_harness.py <project-root>
```
