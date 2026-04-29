#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import narration_pipeline

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
narration_pipeline.run("SessionEnd", payload)

# Mark session as ended in INDEX.md (best-effort)
try:
    import index_io
    import project_root
    from pathlib import Path

    cwd_raw = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "") or os.environ.get("PWD", "")
    if cwd_raw:
        cwd = project_root.find_project_root(cwd_raw)
        sd = Path(cwd) / ".claude" / "sessions" / payload.get("session_id", "")
        idx = index_io.read_index(sd)
        if idx:
            idx["last_updated"] = idx.get("last_updated", "") + " (ended)"
            content = (sd / index_io.INDEX_NAME).read_text(encoding="utf-8")
            _, body = index_io.parse_frontmatter(content)
            index_io.atomic_write(sd / index_io.INDEX_NAME, index_io.serialize(idx, body))
except Exception:
    pass

sys.exit(0)
