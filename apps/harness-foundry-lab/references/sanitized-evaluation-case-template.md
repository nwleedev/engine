# Sanitized Evaluation Case Template

Use this template when an evaluation finding may become a `harness-foundry` synthetic corpus sample or validator rule.

## Summary

- Source project type:
- Harness domain:
- Work type:
- Failure mode:
- Proposed rule or corpus sample:

## Sanitized reproduction

Provide the smallest synthetic `docs/domain-harness/**` tree that reproduces the failure. Replace company names, product names, customer details, private code, internal documents, credentials, and identifiers with neutral examples.

## Removed information

| category | removed or replaced | replacement |
|---|---|---|
| secrets or credentials | yes/no | neutral placeholder |
| customer data | yes/no | synthetic organization |
| private source code | yes/no | simplified pseudocode |
| internal documents | yes/no | public-safe summary |
| strategy or roadmap | yes/no | generic scenario |

## Public-safety review

- `public_safety_check`: not yet reviewed
- Reviewer:
- Review date:

## Corpus acceptance criteria

- The case is public-safe synthetic content.
- The sample has one primary expected failure.
- The expected `rule_id` is deterministic.
- The case improves a validator, template, report, or skill boundary.
- The case does not require access to the original project.
