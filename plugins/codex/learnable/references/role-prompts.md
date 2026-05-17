<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/references/role-prompts.md -->

# Role Prompts

Learnable owns these role responsibilities even when optional shared-subagents are unavailable. If optional shared plugins are unavailable, Learnable performs the same checks in the main session.

- project-mapper -> optional code-mapper: map target files, symbols, call paths, and ownership boundaries.
- docs-verifier -> optional docs-researcher: verify official API/library/framework behavior.
- material-writer -> main-session fallback: write concise Markdown material from approved evidence.
- material-curator -> main-session fallback: organize session graph, title, parent, child, and source refs.
- accuracy-reviewer -> optional citation-verifier or reviewer: check claims against source refs and counterevidence.
- security-reviewer -> optional security-auditor: check sensitive data, path boundary, prompt leakage, and token leakage.
