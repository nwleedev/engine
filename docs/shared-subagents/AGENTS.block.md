<!-- SHARED-SUBAGENTS-START -->
## Shared Subagents

- Spawn subagents only when the user explicitly asks for subagents, delegation, or parallel agent work.
- Keep simple or single-file work in the main session unless delegation is explicitly requested.
- Use subagents for broad, parallelizable work; treat this block as a routing shim and follow the matching shared-subagents role instructions or `references/superpowers-routing.md`.
- Use `context-manager`, `code-mapper`, `docs-researcher`, `source-researcher`, and `citation-verifier` for context, codebase mapping, documentation, source, and evidence checks.
- Use `spec-coverage-reviewer`, `completion-claim-reviewer`, `requirements-reviewer`, `plan-reviewer`, `test-adequacy-reviewer`, `closure-reviewer`, and `risk-reviewer` for review gates.
- Keep reviewer/code-reviewer/security-auditor gates separate with `reviewer`, `code-reviewer`, and `security-auditor`; use main-session fallback prompts when shared-subagents is not installed or the runtime does not expose subagents, and keep `agents.max_depth = 1` unless explicitly approved.
<!-- SHARED-SUBAGENTS-END -->
