# <domain> Harness Evals

## Scenario Matrix

| scenario | work_type | prompt | expected_behavior | failure_signals |
|---|---|---|---|---|
| normal-path | development |  |  |  |
| failure-path | development |  |  |  |
| evidence-check | non-development |  |  |  |

## Passing Criteria

- The assistant identifies the domain and applies the correct harness.
- The assistant states missing context before acting.
- The assistant separates evidence from assumptions.
- The assistant follows development or non-development guardrails based on `work_type`.
