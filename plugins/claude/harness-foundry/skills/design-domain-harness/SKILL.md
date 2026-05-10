<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/harness-foundry/skills/design-domain-harness/SKILL.md -->

---
name: design-domain-harness
description: Use when turning a selected project domain into a domain-harness spec with components, guardrails, and eval scenarios.
metadata:
  short-description: Design a domain harness spec
---

# Design Domain Harness

## Workflow

1. Confirm the selected domain, owner, `work_type`, and repeated work the harness must support.
2. Read `references/domain-harness-template.md` before drafting the spec structure.
3. Read `references/risk-checklist.md` before defining development, non-development, or mixed guardrails.
4. Read `references/evaluation-template.md` before proposing eval scenarios.
5. Design the full domain-harness, including skills, subagents, rules, hooks, MCP guidance, evals, and guardrails where relevant.
6. Separate approved current scope from future optional components.

## Output

- Domain harness spec draft
- Evidence-backed scope and non-goals
- Inputs and outputs
- Component recommendations
- Guardrails
- Evaluation scenarios
- Open questions

## Do not

- Do not reduce the harness to skills-only unless the user explicitly chooses that scope.
- Do not invent domain needs without project evidence.
- Do not activate agents, MCP servers, hooks, or AGENTS.md rules.
