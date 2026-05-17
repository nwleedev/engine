<!-- SHARED-SUBAGENTS-START -->
## Shared Subagents

- Spawn subagents only when the user explicitly asks for subagents, delegation, or parallel agent work.
- Keep simple or single-file work in the main session unless delegation is explicitly requested.
- Use subagents for broad, parallelizable work such as codebase mapping, documentation checks, requirement review, plan review, spec coverage review, evidence verification, test adequacy review, completion claim review, risk review, correctness review, code-health review, and security audit.
- Use `spec-coverage-reviewer` for Spec Ledger and Spec-to-Plan Coverage Matrix fidelity.
- Use `completion-claim-reviewer` before claiming implementation or review work is complete when spec coverage, Fixture Governance Contract, validator evidence, or not-run items could affect the claim.
- Keep reviewer/code-reviewer/security-auditor gates separate when correctness, maintainability, and security all need review.
- Use main-session fallback prompts when shared-subagents is not installed or the runtime does not expose subagents.
- Keep `agents.max_depth = 1` unless explicitly approved.
<!-- SHARED-SUBAGENTS-END -->
