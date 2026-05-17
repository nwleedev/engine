# Learnable Policy

Learnable is local-only in the MVP. Materials live under `.codex/materials`; browser UI reads saved material and does not generate new material.

Durable invariants:

- Do not create browser-originated ask/explain/job APIs in MVP.
- `.codex/materials`만 쓰는 턴에서는 자동 checkpoint를 하지 않는다. 사용자가 저장을 명시적으로 요청하거나 material 외 repo 작업이 포함되면 일반 session-memory 정책을 따른다.
- Do not call `$session-memory:checkpoint` for `.codex/materials`-only material generation unless the user explicitly asks.
- Do not create, mutate, migrate, or clean `.codex/session-memory`; Learnable material storage is separate.
- Do not expose tokens, private material paths, `.env` values, or prompt leakage in CLI, API, Markdown, events, audits, or logs.
- Treat shared-skills/shared-subagents as optional enhancements; Learnable must work without them.
