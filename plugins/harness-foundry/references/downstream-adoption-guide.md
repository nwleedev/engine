# Downstream Adoption Guide

Use this guide when applying `harness-foundry` to a real downstream project. The goal is to diagnose first, write only approved artifacts, and keep project-local evidence separate from upstream plugin improvements.

## Adoption Models

| model | execution location | use when | tradeoff |
|---|---|---|---|
| Operator-run | Run `harness-foundry` scripts from engine or a plugin cache against a target project root. | You need a safe v1 default that does not copy tooling into the project. | Harder to wire directly into CI. |
| Project-local tooling | Copy approved tooling into the target project. | The team wants CI or onboarding checks owned by the project. | The project must manage updates and version drift. |
| Plugin-mediated workflow | Use installed Codex skills to guide diagnosis, scaffold planning, audit, and report drafting. | The team already uses Codex with this plugin enabled. | Depends on the Codex/plugin environment. |

Operator-run is the default v1 adoption model.

## Phase 0: Preconditions

Confirm the target project root, owner, adoption purpose, branch state, dirty worktree state, and privacy policy. Read existing AGENTS.md, MCP configuration, hooks, subagents, and GitHub templates without modifying them.

## Phase 1: Read-only Diagnosis

Use `diagnose-project` to identify candidate domains, work types, owners, risks, and whether the project needs development, non-development, or mixed harnesses. If `docs/domain-harness/index.md` exists, read it as the source of truth. If it does not exist, record the missing registry as a scaffold candidate only.

## Phase 2: Harness Drafting

Use `design-domain-harness` and `update-registry` to draft `spec.md`, `evals.md`, `scaffold.md`, and registry rows. Runtime behavior changes belong in scaffold plans until separately approved.

## Phase 3: Approved Scaffold

Before creating or editing target project files, present the file list, diff preview, rollback note, and approval gates. `docs/domain-harness/**` files require explicit approval before writing. AGENTS.md, MCP configuration, hooks, subagents, and GitHub templates require separate explicit approval before modification or activation.

## Phase 4: Validator Run

Run the validator against the target project root:

```bash
rtk python3 <harness-foundry-path>/scripts/validate_domain_harness.py <project-root>
rtk python3 <harness-foundry-path>/scripts/validate_domain_harness.py <project-root> --json
```

Exit code `0` means the deterministic structure check passed. Exit code `1` means findings should be reviewed and usually converted into an improvement report draft. Exit code `2` means the path or execution environment must be fixed first.

## Phase 5: Improvement Report

Generate a report draft from validator JSON:

```bash
rtk python3 <harness-foundry-path>/scripts/summarize_domain_harness_failures.py validation.json
```

Downstream reports are project-local artifacts. Save approved reports at:

```text
docs/domain-harness/reports/<date>-improvement-report.md
```

Do not write report files automatically. Review the draft first, complete `privacy_sanitization_check`, and remove secrets, credentials, customer data, private source code, and internal documents before sharing outside the project.

## Phase 6: Local vs Upstream

Separate local fixes from upstream regression candidates.

| category | handling |
|---|---|
| local harness issue | Fix the target project's registry, spec, evals, or scaffold. |
| upstream plugin issue | Create a sanitized synthetic regression case for `harness-foundry`. |
| runtime activation issue | Check approval records and current AGENTS.md, MCP, hooks, or subagent activation state. |
| non-development quality issue | Review source quality, privacy, brand or tone, and approval flow. |
| security/privacy issue | Stop upstream sharing and keep remediation project-local. |

Do not copy downstream project source, customer data, internal documents, or credentials into upstream fixtures.

## Phase 7: Optional GitHub Templates

GitHub issue and PR templates remain passive assets until explicit approval. If approved, compare existing `.github/**` files, show a diff preview, and only then copy templates into `.github/ISSUE_TEMPLATE/*.yml` or `.github/pull_request_template.md`.

## Phase 8: Operating Loop

Re-run the loop when a validator failure, AI work incident, new domain, technology change, business process change, or privacy/security policy change appears. Update `last_reviewed` when a harness review is complete.

## Approval Gates

These actions always require separate explicit approval:

- Creating or editing `docs/domain-harness/**`.
- Installing `.github/**` issue or PR templates.
- Editing AGENTS.md.
- Adding or changing MCP configuration.
- Creating or activating hooks.
- Creating or activating subagents.
- Creating upstream issues or PRs.
- Moving downstream project information into upstream fixtures.
