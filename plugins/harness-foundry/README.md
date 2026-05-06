# harness-foundry

Codex-first skills for designing project-specific domain harnesses.

## Purpose

`harness-foundry` helps teams diagnose a project, design domain-specific AI work environments, maintain a human-readable registry, plan safe scaffolding, and audit existing harness artifacts.

## Boundaries

- v1 is skill-only.
- It does not install agents, MCP servers, hooks, or AGENTS.md rules automatically.
- It does not bulk-install public awesome repositories.
- It supports development, non-development, and mixed work.
- Downstream reports are project-local artifacts.
- GitHub issue and PR templates are passive assets until explicitly approved for installation in a target project.

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
rtk python3 plugins/harness-foundry/scripts/validate_domain_harness.py plugins/harness-foundry/fixtures/domain-harness/valid-dev
rtk pytest plugins/harness-foundry/tests
```

## Downstream Quality Loop

In a target project, use `docs/domain-harness/index.md` as the source of truth. Run the validator against the project root:

```bash
rtk python3 plugins/harness-foundry/scripts/validate_domain_harness.py <project-root> --json
```

Then convert the JSON into an improvement report draft:

```bash
rtk python3 plugins/harness-foundry/scripts/summarize_domain_harness_failures.py validation.json
```

The report draft is reviewed before writing it to the target project. If saved, the recommended location is:

```text
docs/domain-harness/reports/<date>-improvement-report.md
```

Only sanitized, public-safe cases should become upstream `harness-foundry` fixture candidates.
