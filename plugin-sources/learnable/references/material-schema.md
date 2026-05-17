# Material Schema

Learnable stores each material in `.codex/materials/sessions/<learnable_session_id>/nodes/<node_id>/`.

Required files:

- `session.json`: session metadata, root node id, status, timestamps, provenance.
- `graph.json`: node map and parent-child edges for a session.
- `nodes/<node_id>/material.json`: material metadata, title, parent node, `source_refs`, redacted prompt, timestamps, provenance.
- `nodes/<node_id>/node.md`: Markdown body.
- `events.jsonl`: redacted append-only material events.

Material writes must validate schema, graph integrity, source evidence, and Markdown body before mutating storage. If validation fails, return answer-only guidance or candidate choices instead of partial writes.
