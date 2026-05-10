---
name: update-registry
description: Use when creating or updating docs/domain-harness/index.md as the human-readable registry for domain harnesses.
metadata:
  short-description: Update domain harness registry
---

# Update Registry

## Workflow

1. Read `references/registry-template.md` when creating a new registry.
2. Read the existing `docs/domain-harness/index.md` before changing rows.
3. Add or update rows only for harnesses with an identified domain, `work_type`, status, owner, spec path, eval path, scaffold path, and review date.
4. Prefer explicit `draft`, `active`, or `deprecated` status over ambiguous wording.
5. Keep paths relative to `docs/domain-harness/`.

## Output

- Updated registry row or proposed registry patch
- Missing metadata
- Broken or unverified links
- Follow-up actions

## Do not

- Do not create or maintain `index.json` as a source of truth in v1.
- Do not delete deprecated harnesses without explicit approval.
- Do not mark a harness active when required spec, evals, or scaffold files are missing.
