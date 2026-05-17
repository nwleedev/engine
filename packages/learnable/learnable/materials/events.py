from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from learnable.core.redaction import redact_text


_SENSITIVE_KEYS = frozenset(
    {"authorization", "api_key", "apikey", "key", "password", "secret", "token"}
)


def append_event(
    events_path: Path,
    *,
    event_type: str,
    learnable_session_id: str,
    message: str,
    node_id: str | None = None,
) -> None:
    """Append a redacted material session event JSONL record."""

    record: dict[str, object] = {
        "created_at": utc_now(),
        "type": event_type,
        "learnable_session_id": learnable_session_id,
        "message": redact_text(message),
    }
    if node_id is not None:
        record["node_id"] = node_id
    _append_jsonl(events_path, record)


def append_audit(
    audit_path: Path,
    *,
    request: Mapping[str, object],
    action: Mapping[str, object],
) -> None:
    """Append a redacted server audit JSONL record without secret values."""

    record = {
        "created_at": utc_now(),
        "request": _sanitize(request),
        "action": _sanitize(action),
    }
    _append_jsonl(audit_path, record)


def read_events(events_path: Path) -> list[dict[str, object]]:
    """Read material session event JSONL records in append order."""

    return _read_jsonl(events_path, "event")


def read_audits(audit_path: Path) -> list[dict[str, object]]:
    """Read server audit JSONL records in append order."""

    return _read_jsonl(audit_path, "audit")


def _read_jsonl(path: Path, record_name: str) -> list[dict[str, object]]:
    if not path.exists() or path.read_text(encoding="utf-8") == "":
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{record_name} JSONL record must be an object")
        records.append(record)
    return records


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _append_jsonl(path: Path, record: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    with _file_lock(path.with_name(f".{path.name}.lock")):
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        _atomic_write_text(path, existing + line)


@contextmanager
def _file_lock(path: Path):
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write_text(path: Path, text: str) -> None:
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_parent_dir(path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _fsync_parent_dir(path: Path) -> None:
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _sanitize(value: object) -> object:
    if isinstance(value, Mapping):
        cleaned: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in _SENSITIVE_KEYS:
                continue
            cleaned[key_text] = _sanitize(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
