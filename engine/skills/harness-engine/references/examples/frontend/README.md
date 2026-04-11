# Frontend Reference Example Pack

This directory contains reference-only evidence distilled from this repository's legacy frontend harness and direct examples.

Purpose:

- Shows the level of direct examples and validation rigor a frontend harness should have.
- Helps quickly recall which Anti/Good pairs are needed for common combinations like `React`, `TanStack Query`, and `React Hook Form`.
- Shows the density at which public APIs, layer rules, and cross-imports should be documented in projects adopting Feature Sliced Design (FSD).
- Serves as a few-shot reference to supplement the thin frontend adapter and project contract packet.

Rules:

- The content here is not portable core to be copied as-is to new projects.
- Content that does not match the project stack should be referenced only and discarded.
- Sources and rules for the final document are always re-confirmed against the project's official documentation and actual code.
- This directory is not a baseline for minimum contracts. Minimum contract determination prioritizes common phase, adapter, and contract packet criteria.

Related legacy evidence documents:

- `.claude/skills/harness-fe-tanstack-query.md`
- `.claude/skills/harness-fe-react-hook-form.md`
- `.claude/skills/harness-fe-testing.md`
- `.claude/skills/harness-fe-testing.md`
- `.claude/skills/harness-fe-fsd.md`
