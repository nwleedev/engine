# harness-foundry

Codex-first skills for designing project-specific domain harnesses.

## Purpose

`harness-foundry` helps teams diagnose a project, design domain-specific AI work environments, maintain a human-readable registry, plan safe scaffolding, and audit existing harness artifacts.

## Boundaries

- v1 is skill-only.
- It does not install agents, MCP servers, hooks, or AGENTS.md rules automatically.
- It does not bulk-install public awesome repositories.
- It supports development, non-development, and mixed work.

## Included Skills

- `diagnose-project`
- `design-domain-harness`
- `update-registry`
- `scaffold-domain-harness`
- `audit-domain-harness`

## Verification

Run:

```bash
rtk python3 plugins/harness-foundry/scripts/validate_harness_foundry.py
rtk pytest plugins/harness-foundry/tests
```
