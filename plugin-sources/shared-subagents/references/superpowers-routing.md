# Superpowers Common Subagent Routing

## Principles

- Use shared custom agent names directly when the runtime supports them.
- When custom agent names are unavailable, inject role instructions into `explorer`, `worker`, or `default`.
- Keep `agents.max_depth = 1`.
- Start with 3-4 concurrent agents unless the task clearly needs more.

## Stage Routing

| Superpowers stage | Preferred agent | Fallback |
|---|---|---|
| brainstorming | `source-researcher`, `requirements-reviewer` | `explorer` with source/requirements prompt |
| writing-plans | `context-manager`, `requirements-reviewer`, `plan-reviewer` | `explorer` with context/plan prompt |
| subagent-driven-development start | `context-manager`, `code-mapper` | `explorer` with mapping prompt |
| API or library verification | `docs-researcher` | `explorer` with docs verification prompt |
| source evidence review | `source-researcher`, `citation-verifier` | `explorer` with source/citation verification prompt |
| requirements fidelity review | `requirements-reviewer` | `default` with Requirement Packet review prompt |
| plan fidelity review | `plan-reviewer` | `default` with Plan Contract review prompt |
| spec coverage review | `spec-coverage-reviewer` | `default` with Spec Ledger and Spec-to-Plan Coverage Matrix review prompt |
| test reconciliation review | `test-reconciliation-reviewer` | `default` with test reconciliation and artifact drift review prompt |
| test adequacy review | `test-adequacy-reviewer` | `default` with newly written or modified test adequacy review prompt |
| completion claim review | `completion-claim-reviewer` | `default` with Coverage Report, Verification Gate, and Evidence Bundle review prompt |
| closure review | `closure-reviewer` | `default` with Closure Report review prompt |
| risk review | `risk-reviewer` | `default` with Risk Register review prompt |
| correctness review | `reviewer` | `default` with PR review prompt |
| code quality review | `code-reviewer` | `default` with code-health review prompt |
| security review | `security-auditor` | `default` with security review prompt |

## Fallback Prompt Rules

Every fallback prompt must include these constraints.

- Perform exactly one assigned role.
- Read only the files and evidence needed for that role.
- Do not edit code unless the parent explicitly grants write scope.
- Return only findings, evidence, risks, and next action.
- Route out-of-scope questions back to the parent agent.

## Do Not

- Do not use `source-researcher` for implementation decisions.
- Do not use `docs-researcher` for market or strategy judgment.
- Do not use `requirements-reviewer` or `plan-reviewer` for implementation code-quality review.
- Do not use `plan-reviewer` as a substitute for `spec-coverage-reviewer` when clause-level coverage is required.
- Do not use `test-adequacy-reviewer` for existing test relevance, reconciliation evidence, artifact drift, or broad correctness review.
- Do not use `test-reconciliation-reviewer` for newly written or modified test assertion quality when no existing-test reconciliation or artifact drift evidence is in scope.
- Route reconciliation/current-coverage test plans, related test results, stale/obsolete/contradictory/orphan/false-confidence coverage claims, and deletion/demotion/quarantine evidence to `test-reconciliation-reviewer`.
- Route new/modified test plans, related test results, assertion quality, behavior boundary coverage, fixture/mock justification, determinism, and executable test adequacy to `test-adequacy-reviewer`.
- Do not use `closure-reviewer` as a substitute for `completion-claim-reviewer` when a done claim depends on coverage reports, validator exit code, or fixture governance.
- Do not ask `reviewer` and `code-reviewer` the same question in parallel.
- Do not modify the Superpowers plugin cache during installation.
