<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-subagents/README.md -->

# Shared Subagents

Shared Claude Code agent templates rendered from the canonical shared-subagents role definitions.

## Agent Roles

- `context-manager`, `code-mapper`, and `docs-researcher` gather project context, code structure, and official documentation evidence.
- `source-researcher`, `requirements-reviewer`, `plan-reviewer`, and `citation-verifier` keep source, requirements, plan, traceability, and citation checks separate.
- `test-adequacy-reviewer`, `closure-reviewer`, and `risk-reviewer` review test quality, verification-gate evidence, residual risk, rollback, fallback, and unverifiable items.
- `reviewer`, `code-reviewer`, and `security-auditor` remain separate gates for correctness/behavior regression/contract review, maintainability/design/readability, and security-audit review.

## Claude Bundle Notes

- This bundle contains generated Claude agent Markdown files under `agents/`.
- Codex-only installer and scaffold helpers are intentionally omitted from this Claude bundle.
- Use the plugin through Claude Code's normal plugin loading and agent discovery flow.
- If your Claude Code environment discovers plugin-bundled agents directly, invoke them by name. If it requires project-local agents, copy the needed Markdown files into `.claude/agents/` and restart Claude Code.
- Example: `Use the test-adequacy-reviewer subagent to review tests for AC-001 / SCN-001.`
- Keep runtime-specific MCP configuration in the user or project tool configuration that owns those servers.

## Superpowers Integration

Use `references/superpowers-routing.md` for stage routing and fallback role guidance when custom agent names are unavailable.
