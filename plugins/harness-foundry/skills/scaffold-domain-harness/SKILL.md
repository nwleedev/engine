---
name: scaffold-domain-harness
description: Use when a domain-harness spec is approved and needs a safe scaffold plan for project-local skills, subagents, rules, hooks, MCP guidance, and eval files.
metadata:
  short-description: Plan safe harness scaffolding
---

# Scaffold Domain Harness

## Workflow

1. Read the approved domain-harness spec and registry row.
2. Identify the files that may be created for specs, evals, scaffold plans, project-local skills, subagents, rules, hooks, and MCP guidance.
3. Split changes into safe phases with separate approval points for configuration that changes runtime behavior.
4. Produce a scaffold plan before writing or activating anything.
5. Treat GitHub issue and PR templates as passive assets unless the user explicitly approves copying them into the target project.
6. Include verification commands and rollback notes for each phase.

## Output

- Scaffold plan
- File tree
- Approval gates
- Verification checklist
- Risks and rollback notes

## Boundaries

AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval before modification or activation.

GitHub issue and PR templates require separate explicit approval before copying them into a downstream project `.github/**` location.

## Do not

- Do not automatically modify AGENTS.md.
- Do not automatically install MCP servers.
- Do not activate hooks or subagents without explicit approval.
- Do not install GitHub issue or PR templates without explicit approval.
