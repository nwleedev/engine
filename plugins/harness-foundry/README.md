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

Report drafts are not auto-saved. Complete `privacy_sanitization_check` and get explicit approval before saving or sharing downstream reports.

Only sanitized, public-safe cases should become upstream `harness-foundry` fixture candidates.

## Downstream Adoption Models

| model | default | notes |
|---|---|---|
| Operator-run | yes | Run `harness-foundry` scripts from engine or a plugin cache against a target project root. |
| Project-local tooling | no | Copy tooling into a target project only after explicit approval. |
| Plugin-mediated workflow | no | Use installed Codex skills when the team already works through Codex. |

Operator-run is the recommended v1 starting point because it avoids copying tooling into the target project before the team approves project-local files.

GitHub issue and PR templates, AGENTS.md changes, MCP configuration, hooks, and subagents require separate explicit approval before installation, modification, or activation.

See `references/downstream-adoption-guide.md` for the full downstream adoption process.
