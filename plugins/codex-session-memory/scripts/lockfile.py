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


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_ino == right.st_ino and left.st_dev == right.st_dev


def _remove_dead_lock(path: Path) -> bool:
    try:
        stale_stat = path.stat()
    except FileNotFoundError:
        return False
    if not _lock_process_is_dead(path):
        return False
    try:
        current_stat = path.stat()
    except FileNotFoundError:
        return False
    if not _same_file(stale_stat, current_stat):
        return False
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


@contextmanager
def acquire_lock(path: Path, timeout_seconds: float = 5.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _remove_dead_lock(path):
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
