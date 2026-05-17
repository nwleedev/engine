<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/references/server-workflow.md -->

# Server Workflow

Learnable serves saved material through a local, read-only web viewer. The server is an inspection surface for `.codex/materials`, not a prompt execution surface.

Startup contract:

- Use `learnable serve --backend auto --host 127.0.0.1 --port <port>` after material storage exists.
- Prefer `127.0.0.1` unless the user explicitly asks for another bind address.
- Treat the server token as local control data and do not print it in user-facing material.
- Use `learnable stop --token-file .codex/materials/.server/token` for graceful shutdown.

Read-only route contract:

- `GET /` serves the static viewer shell.
- `GET /assets/app.css` and `GET /assets/app.js` serve local assets only.
- `GET /api/status`, `GET /api/sessions`, `GET /api/materials/tree`, and `GET /api/materials/node` read saved material state.
- `POST /api/server/reload` refreshes in-memory indexes without creating material.
- `POST /api/server/shutdown` requests local shutdown with the server token.

MVP exclusions:

- Do not add browser prompt input UI.
- Do not add `/api/ask`, `/api/explain`, or browser-originated job APIs.
- Do not create `.codex/materials` from read-only GET/status/sessions requests.
- Do not expose private material paths, token values, prompt text, or source excerpts that violate the source policy.

Verification checklist:

- Desktop and mobile layouts render without horizontal overflow.
- Markdown viewer, file-system tree, metadata, source refs, prerequisites, hierarchy, and local status regions are present.
- Browser console has no errors during first load and reload.
- Shutdown completes and leaves no long-running server process.
