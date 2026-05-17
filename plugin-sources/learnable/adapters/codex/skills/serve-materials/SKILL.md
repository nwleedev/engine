---
name: serve-materials
description: Use when a user wants to open, inspect, validate, or troubleshoot the local Learnable material viewer.
---

# Serve Materials

Use the [read-only server workflow](../../../../references/server-workflow.md). Read [policy](../../../../references/policy.md) for shared plugin and session-memory boundaries. Start with `learnable serve --backend auto --host 127.0.0.1 --port <port>` after material storage exists, then open the local URL.

The viewer is read-only. It must not provide browser prompt generation, browser-originated jobs, or `/api/ask` and `/api/explain` write flows in MVP.

Use `learnable stop --token-file .codex/materials/.server/token` to request shutdown.

Shared plugins are optional; when they are unavailable, troubleshoot the viewer in the main session.
