---
name: entry
description: Use when a user asks Learnable to explain project code, functions, files, workflows, or saved material as a local learning artifact.
---

# Learnable Entry

Route Learnable requests without assuming a current Codex thread is the material session. Read [entry routing](../../../../references/entry-routing.md) when mode, target, audience, or source policy is unclear. Read [policy](../../../../references/policy.md) for session-memory and shared plugin boundaries. Read [role prompts](../../../../references/role-prompts.md) when optional review or mapping roles are unavailable.

Inputs this skill may receive: `prompt`, `project_dir`, `target_path`, `target_symbol`, `learnable_session_id`, `parent_node_id`, `audience_level`, `output_mode`, and `source_policy`.

Default routing:

1. Resolve the target with `map-project` when the request names code, "이 함수", a file, or a symbol.
2. Use `check-docs` when claims depend on external APIs, libraries, frameworks, or current behavior.
3. Use `write-material` only when `output_mode` is `material` and evidence is sufficient.
4. Use `organize-materials` when linking a child to `learnable_session_id` and `parent_node_id`.
5. Use `verify-material` before saving or presenting a material as verified.
6. Use `serve-materials` when `output_mode` is `serve`.

Ambiguity policy: for requests like "이 함수", use prior conversation, selected file, cursor context, explicit path, and explicit symbol as evidence. If the target remains ambiguous, ask a confirmation question or present candidates before creating material.

`answer-only` and `outline` modes must answer without mutating `.codex/materials` unless the user explicitly switches to `material` mode.

Shared plugins are optional; session-memory checkpoint boundaries are defined in [policy](../../../../references/policy.md).
