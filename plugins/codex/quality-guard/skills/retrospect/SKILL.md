---
name: retrospect
description: Review the current work turn for superficial fixes, incomplete evidence, skipped verification, or completion claims that are not supported by the work performed.
---

# Retrospect On Superficial Work

Use this skill before finalizing a work turn, especially when code or files changed.

This is not Codex `/review`. `/review` checks a diff for defects. This skill checks whether the current turn's working pattern was superficial.

## Evidence Model

Use the available evidence in this order:

1. Current conversation and visible tool results.
2. AGENTS.md project rules.
3. Project artifacts such as spec, plan, README, generated files, and changed files.
4. `git status --short` and relevant diff output.
5. User-provided summaries or checkpoints.
6. Optional session memory, only when present and clearly connected to the current work.

Do not require `session-memory`. If session memory is missing or appears to belong to a different thread or subagent, mark it as unavailable or mismatch and continue.

## Superficial Work Definition

Treat work as superficial when it handles the visible symptom while avoiding the root cause, verification, or long-term maintainability impact.

Flag these patterns:

- Exceptions are swallowed or errors are hidden instead of fixed.
- Bypass flags, conditional routing, or special-case branches are added around broken logic.
- Only renaming or reformatting was done when behavior change was required.
- An abstraction layer was added over broken code without fixing the broken behavior.
- Values that belong in configuration or domain logic were hardcoded.
- Tests or checks were skipped without a concrete reason.
- Only part of the user request was handled but the result is described as complete.
- Final claims contradict the verification evidence.

Do not flag these as superficial:

- Documentation or wording edits when the user requested documentation or wording edits.
- Explicit sentinel values used as boundary markers.
- Valid configuration changes between known valid options.
- Research or design turns with no code change, when the answer is evidence-backed and scoped honestly.
- Temporary workarounds that clearly state the risk, reason, verification limit, and follow-up action.

## Output

Always use this exact structure:

```text
Context status: complete | reconstructed | incomplete
Superficial risk: none | low | medium | high | unknown
Evidence sources:
- current conversation: used | unavailable
- AGENTS.md: used | unavailable
- project artifacts: used | unavailable
- git status/diff: used | unavailable
- user-provided summary: used | unavailable
- optional session memory: used | unavailable | mismatch
Evidence:
- ...
Root-cause check:
- ...
Next action:
- ...
```

Use `unknown` when evidence is incomplete. Do not lower risk to `none` or `low` just because the available context is compressed or missing.

If risk is `medium`, `high`, or `unknown`, avoid saying the work is complete. Provide one concrete next action.
