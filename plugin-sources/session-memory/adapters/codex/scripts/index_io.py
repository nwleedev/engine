"""INDEX.md frontmatter + body manipulation. Stdlib only."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import tempfile
from typing import Any


_FENCE = "---"
_CONTEXT_HEADING = "## Contexts"
_RESUME_HINT = "Resume this session: `$session-memory:resume {session_prefix}`"


class AtomicIndexWriteError(OSError):
    """INDEX.md replace failed after optional backup creation."""

    def __init__(self, message: str, *, backup_path: Path | None, cause: OSError):
        super().__init__(message)
        self.backup_path = backup_path
        self.__cause__ = cause


def _coerce(v: str):
    s = v.strip()
    if s.lstrip("-").isdigit():
        try:
            return int(s)
        except ValueError:
            pass
    return s


def read_frontmatter(path: Path):
    p = Path(path)
    if not p.is_file():
        return None
    text = p.read_text()
    if not text.startswith(_FENCE):
        return {}
    end = text.find("\n" + _FENCE, len(_FENCE))
    if end < 0:
        return {}
    block = text[len(_FENCE):end].strip()
    out = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = _coerce(v)
    return out


def _split_doc(text: str):
    if not text.startswith(_FENCE):
        return {}, text
    end = text.find("\n" + _FENCE, len(_FENCE))
    if end < 0:
        return {}, text
    fm = {}
    for line in text[len(_FENCE):end].strip().splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = _coerce(v)
    body_start = end + len("\n" + _FENCE)
    return fm, text[body_start:].lstrip("\n")


def _render(fm: dict, body: str) -> str:
    lines = [_FENCE]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append(_FENCE)
    return "\n".join(lines) + "\n\n" + body


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def _index_lock(path: Path):
    """Serialize writers per INDEX.md path."""
    lock_path = path.with_name("INDEX.md.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield lock_path
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _writer_token(writer_id: str | None = None) -> str:
    token = writer_id or str(os.getpid())
    safe_token = "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in token
    )
    return safe_token.strip("-") or "writer"


def _atomic_write(path: Path, text: str, *, writer_id: str | None = None) -> Path | None:
    """Replace INDEX.md atomically; backup files are repair evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = _writer_token(writer_id)
    writer_scope = f"{writer}.{os.getpid()}"
    backup_path = None
    try:
        if path.exists():
            backup_path = path.with_name(f".index.backup.{writer_scope}.md")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        fd, temp_name = tempfile.mkstemp(
            prefix=f".index.tmp.{writer_scope}.",
            suffix=".md",
            dir=path.parent,
            text=True,
        )
        temp_path = Path(temp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            temp_file.write(text)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
        if temp_path.exists():
            temp_path.unlink()
    except OSError as exc:
        try:
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        raise AtomicIndexWriteError(
            f"failed to update {path}",
            backup_path=backup_path,
            cause=exc,
        ) from exc
    return backup_path


def write_index(
    path: Path,
    frontmatter: dict,
    contexts: list,
    *,
    writer_id: str | None = None,
) -> Path | None:
    p = Path(path)
    body_lines = ["# Session Summary", "", "(in progress)", "", _CONTEXT_HEADING, ""]
    for c in contexts:
        body_lines.append(f"- [{c['filename']}] — {c['summary']}")
    body_lines.append("")
    body_lines.append("---")
    session_prefix = str(frontmatter.get("session_id", ""))[:8]
    body_lines.append(_RESUME_HINT.format(session_prefix=session_prefix))
    body_lines.append("")
    with _index_lock(p):
        return _atomic_write(p, _render(frontmatter, "\n".join(body_lines)), writer_id=writer_id)


def append_context_entry(
    path: Path,
    filename: str,
    summary: str,
    *,
    writer_id: str | None = None,
) -> Path | None:
    return append_context_entry_with_frontmatter(
        path,
        filename,
        summary,
        writer_id=writer_id,
    )


def _append_context_entry_locked(
    path: Path,
    filename: str,
    summary: str,
    *,
    writer_id: str | None = None,
    frontmatter_updates: dict[str, Any] | None = None,
) -> Path | None:
    p = Path(path)
    with _index_lock(p):
        if p.exists():
            fm, body = _split_doc(p.read_text(encoding="utf-8"))
        else:
            fm, body = {}, "# Session Summary\n\n(in progress)\n\n## Contexts\n\n---\n"
        fm.update(frontmatter_updates or {})
        if "session_id" in fm:
            body = _ensure_resume_hint(body, str(fm.get("session_id", ""))[:8])
        lines = body.splitlines()
        try:
            h = lines.index(_CONTEXT_HEADING)
        except ValueError:
            lines.extend([_CONTEXT_HEADING, ""])
            h = len(lines) - 2
        insert_at = h + 2
        while insert_at < len(lines) and lines[insert_at].startswith("- ["):
            insert_at += 1
        lines.insert(insert_at, f"- [{filename}] — {summary}")
        return _atomic_write(
            p,
            _render(fm, "\n".join(lines) + ("\n" if not body.endswith("\n") else "")),
            writer_id=writer_id,
        )


def append_context_entry_with_frontmatter(
    path: Path,
    filename: str,
    summary: str,
    *,
    writer_id: str | None = None,
    **updates,
) -> Path | None:
    return _append_context_entry_locked(
        path,
        filename,
        summary,
        writer_id=writer_id,
        frontmatter_updates=updates,
    )


def _ensure_resume_hint(body: str, session_prefix: str) -> str:
    if "Resume this session:" in body:
        return body
    return body.rstrip() + "\n\n---\n" + _RESUME_HINT.format(session_prefix=session_prefix) + "\n"


def update_frontmatter(path: Path, *, writer_id: str | None = None, **updates) -> Path | None:
    p = Path(path)
    with _index_lock(p):
        fm, body = _split_doc(p.read_text(encoding="utf-8") if p.exists() else "")
        fm.update(updates)
        return _atomic_write(p, _render(fm, body), writer_id=writer_id)
