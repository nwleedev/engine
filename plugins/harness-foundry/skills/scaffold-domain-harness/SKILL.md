---
name: scaffold-domain-harness
description: Use when a domain-harness spec is approved and needs a safe scaffold plan for project-local skills, subagents, rules, hooks, MCP guidance, and eval files.
metadata:
  short-description: Plan safe harness scaffolding
---

# Scaffold Domain Harness

## Workflow

1. Run Phase 0 precondition checks: target project root, owner, purpose, branch state, dirty worktree state, and privacy policy.
2. Read the approved domain-harness spec and registry row.
3. Identify the files that may be created for specs, evals, scaffold plans, project-local skills, subagents, rules, hooks, and MCP guidance.
4. Split documentation scaffold from runtime behavior changes.
5. Produce a scaffold plan before writing or activating anything, including file list, diff preview, rollback note, and approval gates.
6. Keep GitHub issue and PR templates outside the v1 public plugin scaffold flow.
7. Include verification commands and rollback notes for each phase.

## Output

- Scaffold plan
- File tree
- Approval gates
- Verification checklist
- Risks and rollback notes

## Boundaries

AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval before modification or activation.

docs/domain-harness/** files require explicit approval before creation or modification.

GitHub issue and PR templates are outside the v1 public plugin scaffold flow.

## Do not

- Do not automatically modify AGENTS.md.
- Do not automatically install MCP servers.
- Do not activate hooks or subagents without explicit approval.
- Do not install GitHub issue or PR templates from this plugin flow.
- Do not write project-local domain harness files without explicit approval.
