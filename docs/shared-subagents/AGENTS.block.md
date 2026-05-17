<!-- SHARED-SUBAGENTS-START -->
## Shared Subagents

- Spawn subagents only when the user explicitly asks for subagents, delegation, or parallel agent work.
- Keep simple or single-file work in the main session unless delegation is explicitly requested.
- Keep reviewer/code-reviewer/security-auditor gates separate when correctness, maintainability, and security all need review.
- Use main-session fallback prompts when shared-subagents is not installed or the runtime does not expose subagents.
- Keep `agents.max_depth = 1` unless explicitly approved.
<!-- SHARED-SUBAGENTS-END -->
