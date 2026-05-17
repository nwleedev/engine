## Codex Session Memory

- Before ending a work turn, run `$session-memory:checkpoint` when there are changes, decisions, verification results, or remaining tasks to preserve.
- During long work or when MCP/tool usage consumes substantial context, run an intermediate `$session-memory:checkpoint`.
- Immediately after manual or automatic context compaction in the same Codex session, run `$session-memory:resume <current-session-prefix>` as the first action in the next turn.
- Do not auto-resume old sessions when starting a new session. Only resume when the user explicitly calls `$session-memory:resume <prefix>`.
- If the session state is unclear, run `$session-memory:status`.
- If `CODEX_SESSION_ID` is missing, do not checkpoint; report it.
- Use `CODEX_THREAD_ID` only to locate the active Codex rollout transcript, not as the session-memory artifact destination.
- Do not commit `.codex/` session data.
