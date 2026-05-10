"""Per-session narration state: consecutive Haiku failure counter for fallback."""
import json
from pathlib import Path

STATE_FILE = "narration_state.json"
FALLBACK_THRESHOLD = 3


def _path(session_dir: "str | Path") -> Path:
    return Path(session_dir) / STATE_FILE


def _read(session_dir: "str | Path") -> dict:
    p = _path(session_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write(session_dir: "str | Path", state: dict) -> None:
    p = _path(session_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state), encoding="utf-8")


def get_consecutive_failures(session_dir: "str | Path") -> int:
    return int(_read(session_dir).get("consecutive_failures", 0))


def increment_failures(session_dir: "str | Path") -> None:
    s = _read(session_dir)
    s["consecutive_failures"] = int(s.get("consecutive_failures", 0)) + 1
    _write(session_dir, s)


def reset_failures(session_dir: "str | Path") -> None:
    s = _read(session_dir)
    s["consecutive_failures"] = 0
    _write(session_dir, s)


def should_use_fallback(session_dir: "str | Path") -> bool:
    return get_consecutive_failures(session_dir) >= FALLBACK_THRESHOLD
