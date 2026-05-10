"""JSONL append-only diagnostic log for session-memory decisions."""
import json
from datetime import datetime, timezone
from pathlib import Path


def append(path: "str | Path", entry: dict) -> None:
    """Append one JSON line. Silent on failure; diagnostic log must never break callers."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = dict(entry)
        record.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
