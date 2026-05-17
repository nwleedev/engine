---
name: organize-materials
description: Use when Learnable needs to connect root and child materials, update session structure, or explain material graph relationships.
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/adapters/codex/skills/organize-materials/SKILL.md -->


# Organize Materials

Use [session model](../../references/session-model.md). Read [policy](../../references/policy.md) for shared plugin and session-memory boundaries. A root material creates a `learnable_session_id`; a child material must provide `learnable_session_id` and `parent_node_id`.

Keep runtime ids as provenance only. Do not infer a current session from Codex thread ids, terminal ids, or app-server thread ids.

Shared plugins are optional; when they are unavailable, perform the same graph organization in the main session.
