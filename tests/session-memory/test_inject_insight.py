import json, os, sys, io
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import handwrite_context as hw


# ── helpers ──────────────────────────────────────────────────────────

def make_insight_file(path: Path, entries: list[str]) -> None:
    """Write INSIGHT.md using the same format as append_insights_to_project()."""
    content = ""
    for entry in entries:
        content += f"\n---\n**2026-04-01 00:00** · `abc12345`\n\n{entry}\n"
    path.write_text(content, encoding="utf-8")


# ── load_recent_insights ─────────────────────────────────────────────

def test_load_insights_missing_file(tmp_path):
    assert hw.load_recent_insights(str(tmp_path)) == ""


def test_load_insights_empty_file(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "INSIGHT.md").write_text("", encoding="utf-8")
    assert hw.load_recent_insights(str(tmp_path)) == ""


def test_load_insights_fewer_than_max(tmp_path):
    (tmp_path / ".claude").mkdir()
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", ["A", "B", "C"])
    result = hw.load_recent_insights(str(tmp_path), max_entries=20)
    assert "A" in result
    assert "B" in result
    assert "C" in result


def test_load_insights_truncates_to_max(tmp_path):
    (tmp_path / ".claude").mkdir()
    entries = [f"insight-{i}" for i in range(30)]
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", entries)
    result = hw.load_recent_insights(str(tmp_path), max_entries=20)
    assert "insight-0" not in result   # oldest dropped
    assert "insight-29" in result      # newest kept


def test_load_insights_preserves_exact_content(tmp_path):
    (tmp_path / ".claude").mkdir()
    code_insight = "`datetime.utcnow()` → `datetime.now(timezone.utc)` + `.replace(tzinfo=None)`"
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", [code_insight])
    result = hw.load_recent_insights(str(tmp_path))
    assert code_insight in result
