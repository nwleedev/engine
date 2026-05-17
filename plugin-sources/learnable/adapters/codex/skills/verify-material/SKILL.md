---
name: verify-material
description: Use when Learnable material needs evidence, schema, graph, source, or security checks before it is saved or treated as verified.
---

# Verify Material

Check source evidence with [source policy](../../../../references/source-policy.md), security hazards with [security review](../../../../references/security-review.md), and workflow boundaries with [policy](../../../../references/policy.md).

Reject material when:

- claims about external APIs, libraries, frameworks, or current behavior lack sufficient `source_refs`;
- schema, graph, parent, child, or Markdown body requirements fail;
- sensitive data, path boundary, prompt leakage, token leakage, private material paths, or unsafe excerpts are present.

Report a specific blocker and use answer-only output if a safe material write is not possible.

Shared plugins are optional; when they are unavailable, perform the same verification in the main session.
