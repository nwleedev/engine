import os
import time
from pathlib import Path
import retention as rt


def test_archive_old_session(tmp_path):
    sessions = tmp_path / ".claude" / "sessions"
    old = sessions / "old-id"
    old.mkdir(parents=True)
    (old / "INDEX.md").write_text("---\nsession_id: old-id\n---\n", encoding="utf-8")
    old_ts = time.time() - 31 * 86400
    os.utime(old, (old_ts, old_ts))
    os.utime(old / "INDEX.md", (old_ts, old_ts))
    archived = rt.archive_old_sessions(sessions, age_days=30)
    assert "old-id" in archived
    assert not old.exists()
    archive_dir = sessions / "_archive"
    assert any(p.suffix == ".gz" for p in archive_dir.rglob("*"))


def test_does_not_archive_recent_session(tmp_path):
    sessions = tmp_path / ".claude" / "sessions"
    recent = sessions / "recent-id"
    recent.mkdir(parents=True)
    (recent / "INDEX.md").write_text("---\n---\n", encoding="utf-8")
    archived = rt.archive_old_sessions(sessions, age_days=30)
    assert recent.exists()
    assert "recent-id" not in archived


def test_skips_archive_dir(tmp_path):
    sessions = tmp_path / ".claude" / "sessions"
    arch = sessions / "_archive"
    arch.mkdir(parents=True)
    archived = rt.archive_old_sessions(sessions, age_days=30)
    assert archived == []


def test_insight_rotation_when_over_cap(tmp_path):
    insight = tmp_path / ".claude" / "INSIGHT.md"
    insight.parent.mkdir(parents=True)
    entries = "\n---\n".join(f"entry {i}" for i in range(250))
    insight.write_text(entries, encoding="utf-8")
    rotated = rt.rotate_insight(insight, cap=200, move=50)
    assert rotated is not None
    new_count = len([e for e in insight.read_text(encoding="utf-8").split("\n---\n") if e.strip()])
    assert new_count <= 200


def test_insight_no_rotation_under_cap(tmp_path):
    insight = tmp_path / ".claude" / "INSIGHT.md"
    insight.parent.mkdir(parents=True)
    entries = "\n---\n".join(f"entry {i}" for i in range(100))
    insight.write_text(entries, encoding="utf-8")
    rotated = rt.rotate_insight(insight, cap=200, move=50)
    assert rotated is None
