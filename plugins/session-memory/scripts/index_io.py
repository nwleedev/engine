"""Atomic INDEX.md read/write with filename-keyed dedup and rotation detection."""
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

INDEX_NAME = "INDEX.md"
ENTRY_RE = re.compile(r"^- \[([^\]]+)\] — (.*)$", re.MULTILINE)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def _serialize(fm: dict, body: str) -> str:
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines += ["---", ""]
    return "\n".join(lines) + body


def _parse_frontmatter(content: str) -> tuple:
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}, content
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, content[m.end():]


def read_index(session_dir: "str | Path") -> dict:
    p = Path(session_dir) / INDEX_NAME
    if not p.exists():
        return {}
    fm, _ = _parse_frontmatter(p.read_text(encoding="utf-8"))
    return fm


def create_index(session_dir: "str | Path", session_id: str, cwd: str, started_uuid: str = "") -> dict:
    sd = Path(session_dir)
    (sd / "contexts").mkdir(parents=True, exist_ok=True)
    now = _utcnow_iso()
    fm = {
        "session_id": session_id,
        "cwd": cwd,
        "started": now,
        "last_updated": now,
        "last_processed_uuid": "",
        "started_uuid": started_uuid,
        "context_head": "",
        "last_context_written_at": "",
    }
    body = (
        "\n# 세션 요약\n\n(진행 중)\n\n"
        "## 컨텍스트 목록\n\n---\n"
        f"이 세션 재개: `claude -r {session_id}`\n"
    )
    _atomic_write(sd / INDEX_NAME, _serialize(fm, body))
    return fm


def _atomic_write(path: "str | Path", content: str) -> None:
    """Write atomically via tempfile + os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".INDEX.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def update_entry(session_dir: "str | Path", filename: str, one_liner: str,
                 last_uuid: str, new_head: str) -> None:
    """Insert or overwrite the entry keyed by filename. Atomic."""
    sd = Path(session_dir)
    p = sd / INDEX_NAME
    content = p.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(content)

    fm["last_processed_uuid"] = last_uuid
    fm["last_updated"] = _utcnow_iso()
    fm["last_context_written_at"] = _utcnow_iso()
    if new_head:
        fm["context_head"] = new_head

    new_entry_line = f"- [{filename}] — {one_liner}"
    body = _replace_or_insert_entry(body, filename, new_entry_line)
    _atomic_write(p, _serialize(fm, body))


def _replace_or_insert_entry(body: str, filename: str, new_line: str) -> str:
    """Replace the line for `filename` if present; else insert before final --- separator (if any)."""
    lines = body.split("\n")
    out = []
    replaced = False
    for line in lines:
        m = ENTRY_RE.match(line)
        if m and m.group(1) == filename:
            if not replaced:
                out.append(new_line)
                replaced = True
            # skip extra duplicates
        else:
            out.append(line)
    if replaced:
        return "\n".join(out)
    # Insert: find last "---" preceded by a header in body and insert before it
    joined = "\n".join(out)
    # Insert just before the final "---" footer line (the resume hint separator)
    if "\n---\n" in joined:
        idx_pos = joined.rfind("\n---\n")
        return joined[:idx_pos] + "\n" + new_line + joined[idx_pos:]
    return joined + "\n" + new_line + "\n"


def detect_rotation(session_dir: "str | Path", current_first_uuid: str) -> bool:
    """True if started_uuid in INDEX differs from current first message UUID."""
    fm = read_index(session_dir)
    stored = fm.get("started_uuid", "")
    if not stored or not current_first_uuid:
        return False
    return stored != current_first_uuid


def archive_on_rotation(session_dir: "str | Path") -> Path:
    """Rename INDEX.md to INDEX.<old_started_uuid>.md to preserve history."""
    sd = Path(session_dir)
    p = sd / INDEX_NAME
    fm = read_index(sd)
    old_id = fm.get("started_uuid", "unknown")
    archive_path = sd / f"INDEX.{old_id}.md"
    if p.exists():
        os.replace(p, archive_path)
    return archive_path
