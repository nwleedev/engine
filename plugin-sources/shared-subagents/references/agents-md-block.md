<!-- SHARED-SUBAGENTS-START -->
## Shared Subagents

- Use the project-local `.codex/agents` shared subagents installed by `shared-subagents`.
- Spawn subagents only when the user explicitly asks for subagents, delegation, or parallel agent work.
- Use subagents for broad, parallelizable work such as codebase mapping, documentation checks, requirement review, plan review, evidence verification, PR-style review, code-health review, test adequacy review, risk review, and security review.
- Keep simple or single-file work in the main session unless the user explicitly requests delegation.
- Do not delegate urgent blocking work that the main session needs before it can continue.
- Use `context-manager` and `code-mapper` before broad subagent work.
- Use `docs-researcher` for official technical documentation checks, including official comment/documentation format requirements.
- Use `source-researcher` for neutral source collection and Source Ledger preparation without decisions.
- Use `requirements-reviewer` for Requirement Packet fidelity.
- Use `plan-reviewer` for Plan Contract and Traceability Matrix fidelity.
- Use `citation-verifier` for Claim Evidence Map and Source Ledger checks.
- Use `test-adequacy-reviewer` after downstream project test-writing work.
- Use `closure-reviewer` before claiming review findings or completion claims are closed.
- Use `risk-reviewer` for residual risk, rollback, fallback, and unverifiable items.
- Use `reviewer` for correctness, security, and behavior regression review.
- Use `code-reviewer` for maintainability/design/readability review, including comment quality.
- Use `reviewer`, `code-reviewer`, and `security-auditor` as separate review gates.
- Do not ask `reviewer` and `code-reviewer` the same question in parallel; split correctness/security review from maintainability/design review.
- Keep `agents.max_depth = 1` unless explicitly approved.
- Global MCP servers may be inherited by spawned subagents and can increase startup time.
- Keep MCP server configuration in project `.codex/config.toml` or user `~/.codex/config.toml`; shared-subagents does not manage MCP setup.
<!-- SHARED-SUBAGENTS-END -->
