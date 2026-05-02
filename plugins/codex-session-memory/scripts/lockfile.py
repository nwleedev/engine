"""Small cross-process lock based on atomic file creation."""
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _lock_process_is_dead(path: Path) -> bool:
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    try:
        pid = int(metadata.get("pid", 0))
    except (TypeError, ValueError):
        return False
    return not _pid_is_running(pid)


@contextmanager
def acquire_lock(path: Path, timeout_seconds: float = 5.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _lock_process_is_dead(path):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                continue
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
