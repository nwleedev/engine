---
name: write-material
description: Use when Learnable has a confirmed target and enough evidence to draft or save a local Markdown learning material.
---

# Write Material

Follow [material schema](../../../../references/material-schema.md). Read [policy](../../../../references/policy.md) for shared plugin and session-memory boundaries. Write concise Markdown for the selected audience and keep claims tied to source refs.

Before saving:

1. Confirm target, audience, and parent session if any.
2. Confirm source evidence is sufficient for the requested `source_policy`.
3. Produce Markdown with title, explanation, prerequisites when useful, source refs, and follow-up concepts.
4. Run `verify-material`.

Failure handling: Codex execution timeout, insufficient source evidence, or ambiguous target must not produce a partial material write. Return an answer-only explanation, candidate list, or retry instruction rather than mutating `.codex/materials` when the material contract is not satisfied.

Shared plugins are optional; when they are unavailable, write and verify the material in the main session.
