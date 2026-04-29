"""Cold storage of old sessions and INSIGHT.md rotation."""
import shutil
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def archive_old_sessions(sessions_dir: "str | Path", age_days: int = 30) -> List[str]:
    """Tar+gzip sessions older than age_days into _archive/<YYYY-MM>/. Returns archived ids."""
    sessions_dir = Path(sessions_dir)
    if not sessions_dir.exists():
        return []
    cutoff = time.time() - age_days * 86400
    archive_root = sessions_dir / "_archive"
    archived = []
    for session in sessions_dir.iterdir():
        if not session.is_dir():
            continue
        if session.name == "_archive" or session.name.startswith("."):
            continue
        try:
            files = [p for p in session.rglob("*") if p.is_file()]
            mtime = max((p.stat().st_mtime for p in files), default=session.stat().st_mtime)
        except (OSError, ValueError):
            mtime = session.stat().st_mtime
        if mtime >= cutoff:
            continue
        ym = datetime.fromtimestamp(mtime).strftime("%Y-%m")
        target_dir = archive_root / ym
        target_dir.mkdir(parents=True, exist_ok=True)
        tarball = target_dir / f"{session.name}.tar.gz"
        try:
            with tarfile.open(tarball, "w:gz") as tar:
                tar.add(session, arcname=session.name)
            shutil.rmtree(session)
            archived.append(session.name)
        except Exception:
            continue
    return archived


def rotate_insight(insight_path: "str | Path", cap: int = 200, move: int = 50) -> Optional[Path]:
    """If INSIGHT.md exceeds cap entries, move oldest `move` entries to archive file."""
    p = Path(insight_path)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    entries = [e for e in text.split("\n---\n") if e.strip()]
    if len(entries) <= cap:
        return None
    move_count = min(move, max(0, len(entries) - (cap - move)))
    moved = entries[:move_count]
    kept = entries[move_count:]

    ym = datetime.utcnow().strftime("%Y-%m")
    archive_path = p.parent / f"INSIGHT-archive-{ym}.md"
    existing = archive_path.read_text(encoding="utf-8") if archive_path.exists() else ""
    archive_path.write_text(existing + "\n---\n".join(moved) + "\n---\n", encoding="utf-8")
    p.write_text("\n---\n".join(kept), encoding="utf-8")
    return archive_path
