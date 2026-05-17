<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/references/session-model.md -->

# Session Model

`learnable_session_id` is a Learnable material graph id. It is not a Codex thread id, Codex session id, app-server thread id, or terminal id.

Root materials start a session. Child materials require both `learnable_session_id` and `parent_node_id`. Runtime ids can appear only inside provenance fields and must not be used as directory names, graph keys, lookup keys, or implicit current-session selectors.

Organizing materials means preserving parent-child meaning, keeping source refs with the node that uses them, and avoiding cross-session deduplication in the MVP.
