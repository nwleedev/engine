# Downstream Issue Template Guide

`harness-foundry` ships GitHub issue and PR template assets that can be copied into a downstream project after explicit approval.

## Templates

| file | purpose |
|---|---|
| `harness-quality-issue.yml` | Record a project-local harness quality problem. |
| `upstream-regression-case.yml` | Propose a sanitized case that may become an upstream fixture or rule. |
| `harness-feature-request.yml` | Request a new validator rule, report field, template, or domain pattern. |
| `pull_request_template.md` | Review downstream harness edits before merge. |

## Field Rules

- `affected_domain` identifies the domain harness under review.
- `work_type` must be `development`, `non-development`, or `mixed`.
- `validator_output` should include only public-safe excerpts or attach a sanitized report.
- `privacy_sanitization_check` confirms that no secrets, credentials, customer data, private source code, or internal documents are included.
- `local_or_upstream` separates project-local remediation from upstream `harness-foundry` improvements.

## Installation Boundary

Template assets are passive files in this plugin. Copying them into a downstream project `.github/**` directory changes that project workflow and requires explicit user approval.
