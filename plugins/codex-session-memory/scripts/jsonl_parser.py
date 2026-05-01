"""Parse Codex rollout JSONL. Extract user/assistant turn delta from byte offset.
Resilient to malformed lines (skip silently)."""
import json


_KEEP_ROLES = {"user", "assistant"}


def extract_delta(jsonl_path: str, start_offset: int):
    messages = []
    with open(jsonl_path, "rb") as f:
        f.seek(start_offset)
        data = f.read()
        new_offset = start_offset + len(data)

    for raw in data.decode("utf-8", errors="replace").splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "response_item":
            continue
        payload = obj.get("payload") or {}
        role = payload.get("role")
        if role not in _KEEP_ROLES:
            continue
        content = payload.get("content") or []
        if not isinstance(content, list):
            continue
        texts = []
        for item in content:
            if isinstance(item, dict):
                t = item.get("text")
                if isinstance(t, str):
                    texts.append(t)
        if texts:
            messages.append({"role": role, "text": "\n".join(texts)})
    return messages, new_offset
