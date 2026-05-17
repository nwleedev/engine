<!-- SHARED-WORKFLOW-START -->
## Shared Skills And Subagents

- Treat this block as durable project policy; do not invoke a scaffold skill just to recover these instructions.
- Use `shared-skills` workflow skills before and during implementation when requirements, plans, tests, evidence, or completion claims need traceability.
- Use `requirements-packet` before planning if the request has confirmed, inferred, open, or rejected requirements.
- Use `spec-contract` and `plan-contract` before implementation when behavior, interfaces, failure modes, target artifacts, validation methods, fallbacks, or risk levels need to be explicit.
- For behavior-changing implementation, route tests through `scenario-test-designer`, `test-plan-contract`, and `tdd-test-writing`; if automated tests are not feasible, record the reason and residual risk in `verification-gate`.
- Use `implementation-evidence` after changes to connect files, behavior, commands, and requirement/task IDs.
- Use `verification-gate` before claiming work is complete, ready, correct, or decision-ready.
- Use `research-plan`, `source-ledger`, and `claim-evidence-map` for source-backed research and counterevidence review.
- Use shared-subagents plugin-bundled agents when the runtime exposes them; if the runtime requires project-local copies, keep Codex agents in the repository root `.codex/agents/` and Claude Code agents in the repository root `.claude/agents/`.
- Spawn subagents only when the user explicitly asks for subagents, delegation, or parallel agent work.
- Use subagents for broad, parallelizable work such as codebase mapping, documentation checks, requirement review, plan review, evidence verification, PR-style correctness review, code-health review, test adequacy review, risk review, and security audit.
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
- Use `reviewer` for correctness, behavior regression, and contract-change review.
- Use `code-reviewer` for maintainability/design/readability review, including comment quality.
- Use `security-auditor` for security audit, auth, secrets, input validation, and sensitive-data handling.
- Use `reviewer`, `code-reviewer`, and `security-auditor` as separate review gates.
- Do not ask `reviewer` and `code-reviewer` the same question in parallel; split correctness/behavior review, security audit, and maintainability/design review.
- Keep `agents.max_depth = 1` unless explicitly approved.
- Global MCP servers may be inherited by spawned subagents and can increase startup time.
- Keep MCP server configuration in project `.codex/config.toml`, project `.claude/settings.json`, or user-level runtime config; shared-subagents does not manage MCP setup.
<!-- SHARED-WORKFLOW-END -->
