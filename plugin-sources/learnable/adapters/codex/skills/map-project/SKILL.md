---
name: map-project
description: Use when Learnable needs to identify project files, symbols, call paths, ownership boundaries, or likely material targets before writing.
---

# Map Project

Map the target before material writing. Prefer local repository files and current conversation evidence. Read [policy](../../../../references/policy.md) for shared plugin and session-memory boundaries.

Steps:

1. Resolve `project_dir`, `target_path`, and `target_symbol`.
2. Use nearby tests, docs, imports, and callers to explain context.
3. Return candidate targets if more than one target fits.
4. Do not write `.codex/materials` during mapping.

Shared plugins are optional; when they are unavailable, perform the same target mapping in the main session.
