# Domain Harness Registry

This file is the source of truth for project-local domain harnesses.

| domain | work_type | status | owner | spec | evals | scaffold | last_reviewed |
|---|---|---|---|---|---|---|---|
| example-domain | mixed | draft | team-name | `example-domain/spec.md` | `example-domain/evals.md` | `example-domain/scaffold.md` | 2026-05-06 |

## Registry Rules

- Keep this Markdown file as the source of truth.
- Do not maintain `index.json` manually in v1.
- Prefer `deprecated` status over deleting old harness records.
- Each active row must point to existing `spec.md`, `evals.md`, and `scaffold.md`.
