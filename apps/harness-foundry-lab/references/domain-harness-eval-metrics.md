# Domain Harness Eval Metrics

This document defines deterministic v1 validation rules for project-local `docs/domain-harness/**` artifacts.

## Rule Summary

| rule_id | severity | target | pass criteria |
|---|---|---|---|
| `missing-registry` | error | `docs/domain-harness/index.md` | The Markdown registry exists. |
| `registry-parse-error` | error | `docs/domain-harness/index.md` | The registry contains a pipe table with the required columns. |
| `invalid-work-type` | error | registry row | `work_type` is `development`, `non-development`, or `mixed`. |
| `missing-spec-file` | error | active registry row | The referenced `spec.md` exists. |
| `missing-evals-file` | error | active registry row | The referenced `evals.md` exists. |
| `missing-scaffold-file` | error | active registry row | The referenced `scaffold.md` exists. |
| `index-json-source-of-truth` | error | `docs/domain-harness/index.json` | `index.json` is absent or explicitly not the source of truth. |
| `unapproved-auto-hooks` | error | harness artifacts | Harness artifacts do not plan hook activation without explicit approval. |
| `unapproved-auto-mcp` | error | harness artifacts | Harness artifacts do not plan MCP activation without explicit approval. |
| `missing-development-guardrails` | error | `spec.md` | Development harnesses include implementation, testing, security, and dependency guardrails. |
| `missing-non-development-source-policy` | error | `spec.md` | Non-development harnesses include source quality, privacy, tone, and approval guardrails. |
| `missing-mixed-split-guardrails` | error | `spec.md` | Mixed harnesses split development and non-development guardrails. |
| `missing-public-safety-check` | warning | evaluation reports and sanitized evaluation cases | Evaluation reports or sanitized evaluation cases include `public_safety_check` or equivalent text. |

## Registry Contract

The source of truth is `docs/domain-harness/index.md`. v1 supports a simple Markdown pipe table with these columns:

| column | meaning |
|---|---|
| `domain` | Stable harness identifier. |
| `work_type` | `development`, `non-development`, or `mixed`. |
| `status` | `draft`, `active`, or `deprecated`. |
| `owner` | Team or role accountable for review. |
| `spec` | Path to the domain spec, relative to `docs/domain-harness/`. |
| `evals` | Path to the eval file, relative to `docs/domain-harness/`. |
| `scaffold` | Path to the scaffold plan, relative to `docs/domain-harness/`. |
| `last_reviewed` | ISO-like review date or `pending`. |

## Work Type Metrics

Development harnesses must define guardrails for implementation scope, test strategy, security review, and dependency changes.

Non-development harnesses must define source quality, privacy, brand or tone, and approval flow guardrails.

Mixed harnesses must explicitly separate development and non-development guardrails so implementation rules do not silently govern research, planning, communication, or strategy work.

## Public-Safety Metric

`public_safety_check` means the author confirmed that secrets, credentials, customer data, private source code, and internal documents were removed or replaced with neutral synthetic details before an evaluation report or sanitized evaluation case is shared.
