# Evaluation Report Template

Use this template inside `harness-foundry-lab` when evaluation corpus validation needs a maintainer record.

## Summary

- Corpus:
- Report date:
- Trigger:
- Validator command:
- Overall status:

## Affected harnesses

| domain | work_type | status | owner | files reviewed |
|---|---|---|---|---|
| example-domain | mixed | active | team-name | `spec.md`, `evals.md`, `scaffold.md` |

## Findings

| severity | rule_id | path | message |
|---|---|---|---|
| error | example-rule | `docs/domain-harness/index.md` | Describe the problem. |

## Local fix candidates

- Record fixes that should stay inside the evaluated project or corpus sample.
- Include owner, expected file changes, and verification commands.

## Sanitized evaluation case candidates

- Record public-safe cases that may improve `harness-foundry` fixtures, validator rules, templates, or documentation.
- Do not include proprietary code, customer details, internal documents, credentials, or unreleased strategy.

## Public-safety review

- `public_safety_check`: not yet reviewed
- Removed sensitive details:
- Synthetic replacements used:
- Reviewer:

## Verification checklist

- [ ] Validator was run after local edits.
- [ ] Report contains no secrets, credentials, customer data, private source code, or internal documents.
- [ ] Evaluation case candidates were sanitized before sharing outside the project.
- [ ] Open questions have an owner.

## Open questions

- Record unresolved decisions, missing approvals, or risks.
