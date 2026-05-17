"""Locate the current Codex session: thread id, JSONL file, data folder."""
import os
from pathlib import Path


CODEX_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
CHILD_SESSIONS_DIR = "_children"


def current_thread_id():
    v = os.environ.get("CODEX_THREAD_ID", "").strip()
    return v or None


def current_session_id():
    """Return the explicit session-memory artifact target from CODEX_SESSION_ID."""
    v = os.environ.get("CODEX_SESSION_ID", "").strip()
    return v or None


def find_jsonl_by_thread(thread_id: str, codex_sessions_root=None):
    root = Path(codex_sessions_root) if codex_sessions_root else CODEX_SESSIONS_ROOT
    if not root.is_dir():
        return None
    pattern = f"rollout-*-{thread_id}.jsonl"
    matches = sorted(
        root.rglob(pattern),
        key=lambda path: (path.stat().st_mtime_ns, str(path)),
        reverse=True,
    )
    if not matches:
        return None
    return matches[0].resolve()


def data_session_dir(project_root: str, thread_id: str, role: str = "main") -> Path:
    sessions_dir = Path(project_root) / ".codex" / "sessions"
    if role == "child":
        return (sessions_dir / CHILD_SESSIONS_DIR / thread_id).resolve()
    return (sessions_dir / thread_id).resolve()


def artifact_session_dir(project_root: str, thread_id: str) -> Path:
    return Path(project_root) / ".codex" / "session-memory" / "threads" / thread_id


def parent_session_dir(project_root: str, parent_thread_id: str) -> Path:
    return (Path(project_root) / ".codex" / "sessions" / parent_thread_id).resolve()


def child_sessions_dir(project_root: str) -> Path:
    return (Path(project_root) / ".codex" / "sessions" / CHILD_SESSIONS_DIR).resolve()
