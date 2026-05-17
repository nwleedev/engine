# Learnable Codex Adapter

This adapter exposes the Codex-facing Learnable skill entrypoint and its
supporting workflow skills. The canonical user-facing plugin overview remains
in [the Learnable README](../../README.md); this file documents only the Codex
adapter boundary.

## Skills

- `skills/entry/SKILL.md` is the only MVP entrypoint for `$learnable:entry`.
- Supporting skills live under `skills/*/SKILL.md` and keep detailed policy in
  [references](../../references/policy.md) rather than duplicating it in
  `AGENTS.md`.
- The MVP adapter is Codex-only. It does not create a Claude Code adapter or
  `.claude/materials` storage root.

## Runtime Boundary

- Runtime code is packaged from `packages/learnable/learnable/` into the
  generated Codex plugin `_packages/learnable/` directory.
- The default server backend is Python stdlib and must not require FastAPI,
  Starlette, Flask, Uvicorn, Node, or user-project dependencies.
- Browser UI is read-only for MVP and must not expose prompt, follow-up, job, or
  answer-generation surfaces.
