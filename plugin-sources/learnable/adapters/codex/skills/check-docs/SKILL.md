---
name: check-docs
description: Use when Learnable material needs source support for local code, official documentation, external APIs, libraries, frameworks, or web-backed claims.
---

# Check Docs

Use [source policy](../../../../references/source-policy.md) to choose evidence scope. Read [policy](../../../../references/policy.md) for shared plugin and session-memory boundaries.

- `local-only`: use repository files and user-provided context.
- `official-docs`: add official docs for APIs, libraries, frameworks, standards, or cloud services.
- `web-allowed`: broader sources are allowed when authority, recency, and limitations are recorded.

Return source refs with authority and limitations. If evidence is insufficient, report gaps instead of allowing material writes.

Shared plugins are optional; when they are unavailable, perform the same evidence check in the main session.
