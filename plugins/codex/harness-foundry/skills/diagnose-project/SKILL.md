<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/harness-foundry/skills/diagnose-project/SKILL.md -->

---
name: diagnose-project
description: Use when identifying project domains, work types, risks, and AI environment needs before designing a domain harness.
metadata:
  short-description: Diagnose domain harness candidates
---

# Diagnose Project

## Workflow

1. Read project structure, AGENTS.md, docs, package/config files, and existing AI configuration.
2. Identify repeated development, non-development, and mixed workflows.
3. Propose domain-harness candidates only when project evidence supports them.
4. Mark unclear areas as questions instead of inventing domains.

## Output

- Domain candidates
- Evidence
- `work_type`
- Required AI support
- Risks and guardrails
- Priority

## Do not

- Do not create files.
- Do not install skills, subagents, MCP servers, or hooks.
- Do not recommend bulk-installing public awesome repositories.
