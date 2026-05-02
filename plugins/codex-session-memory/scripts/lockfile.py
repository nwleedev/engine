"""Small cross-process lock based on atomic file creation."""
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


@contextmanager
def acquire_lock(path: Path, timeout_seconds: float = 5.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"lock timeout: {path}")
            time.sleep(0.05)
    try:
        metadata = {
            "pid": os.getpid(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        os.write(fd, f"{json.dumps(metadata, sort_keys=True)}\n".encode("utf-8"))
        yield
    finally:
        os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
