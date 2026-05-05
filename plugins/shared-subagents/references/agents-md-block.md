<!-- SHARED-SUBAGENTS-START -->
## Shared Subagents

- Use `context-manager` and `code-mapper` before broad subagent work.
- Use `docs-researcher` for official technical documentation checks.
- Use `online-researcher` only for non-development research such as market, strategy, planning, and ideation.
- Use `spec-reviewer` for requirement, spec, and plan fidelity review.
- Use `reviewer`, `code-reviewer`, and `security-auditor` as separate review gates.
- Keep `agents.max_depth = 1` unless explicitly approved.
- Global MCP servers may be inherited by spawned subagents and can increase startup time.
- Keep MCP server configuration in `~/.codex/config.toml`; shared-subagents does not manage MCP setup.
<!-- SHARED-SUBAGENTS-END -->
