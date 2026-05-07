# harness-foundry

Codex-first skills for designing project-specific domain harnesses.

## Purpose

`harness-foundry` helps teams diagnose a project, design domain-specific AI work environments, maintain a human-readable registry, plan safe scaffolding, and audit existing harness artifacts.

## Boundaries

- v1 is skill-only.
- It does not install agents, MCP servers, hooks, or AGENTS.md rules automatically.
- It does not bulk-install public awesome repositories.
- It supports development, non-development, and mixed work.
- It produces design and scaffold guidance; project file changes require explicit user approval.

## Included Skills

- `diagnose-project`
- `design-domain-harness`
- `update-registry`
- `scaffold-domain-harness`
- `audit-domain-harness`

## Verification

Installed plugin users interact with the public skill surface and project-local
domain harness artifacts. To validate a user project's `docs/domain-harness/**`
files, run the skill-local read-only validator from this repository:

```bash
rtk python3 plugins/harness-foundry/skills/audit-domain-harness/scripts/validate_domain_harness.py <project-root>
```

Maintainer-only plugin package and corpus validation lives in
`apps/harness-foundry-lab`; see that app's README for lab commands.
