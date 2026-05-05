# Awesome Agent Style Benchmark

## Purpose

The goal of the `awesome-*` cross-check is not only to verify fields. It is to understand the structure, length, role boundaries, and guardrail language used by real teams and community-maintained agent collections.

## Samples

- `context-manager`
- `code-mapper`
- `docs-researcher`
- `reviewer`
- `code-reviewer`
- `security-auditor`
- `market-researcher`
- `business-analyst`

## Observation Criteria

- Field set: `name`, `description`, `model`, `model_reasoning_effort`, `sandbox_mode`, `developer_instructions`
- Length: total line count and instruction block line count
- Structure: `Working mode`, `Focus on`, `Quality checks`, `Return`, `Do not`
- Role width: whether each agent has one clear responsibility
- Model routing: model differences between lightweight discovery roles and high-judgment review roles
- Sandbox routing: criteria for read-only and workspace-write agents
- Guardrail language: final sentences that prevent role drift

## Application Criteria

- Each shared agent owns exactly one role.
- Instructions prioritize working mode, focus areas, quality checks, and return format over broad background explanation.
- Each agent ends with guardrail language that prevents role drift.
- `spec-reviewer` and `online-researcher` follow the observed structure while keeping their responsibilities separate.
