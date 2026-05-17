<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/references/entry-routing.md -->

# Entry Routing

Entry accepts: `prompt`, `project_dir`, `target_path`, `target_symbol`, `learnable_session_id`, `parent_node_id`, `audience_level`, `output_mode`, and `source_policy`.

Input contract:

- `prompt`: the user's requested explanation or material goal.
- `project_dir`: defaults to the current project root and must stay inside the repository boundary.
- `target_path`: repository-relative file or directory used to locate the material target.
- `target_symbol`: function, class, method, command, config key, or UI element to explain.
- `learnable_session_id`: existing Learnable material session id used only for child material writes.
- `parent_node_id`: existing material node id required when adding a child material.
- `audience_level`: defaults to `auto` unless the user asks for beginner, maintainer, or operator framing.
- `output_mode`: defaults to `material` when the user asks Learnable to create saved material.
- `source_policy`: one of `local-only`, `official-docs`, or `web-allowed`.

Audience:

- `beginner`: define terms, prerequisites, and learning path.
- `maintainer`: focus on code ownership, contracts, risks, and change impact.
- `operator`: focus on commands, runtime behavior, failure modes, and rollback.
- `auto`: infer from user wording and ask only if ambiguity affects material quality.

Output mode:

- `material`: create or update `.codex/materials` only after target, evidence, schema, and security checks pass.
- `answer-only`: answer in chat and must not mutate `.codex/materials`.
- `outline`: provide structure or candidate material plan and must not mutate `.codex/materials`.
- `serve`: use serve-materials and the read-only server workflow.

Target ambiguity:

- For "이 함수", resolve from prior conversation, selected file, cursor context, explicit path, and explicit symbol.
- If more than one plausible target remains, ask a confirmation question or present candidates before creating material.

Role routing:

- project-mapper handles target discovery before material writing.
- docs-verifier checks official docs when `source_policy` is `official-docs` or `web-allowed`.
- material-writer drafts Markdown only after evidence is adequate.
- material-curator links parent/child nodes and source refs.
- accuracy-reviewer checks source support before saving.
- security-reviewer applies `references/security-review.md`.
