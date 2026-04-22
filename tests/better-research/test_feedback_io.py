# tests/better-research/test_feedback_io.py
import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import feedback_io as fio


# --- load_raw_since_checkpoint ---

def test_load_raw_since_checkpoint_returns_new_entries(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "<!-- checkpoint: 2026-04-22T10:00:00Z -->\n\n"
        "---\nts: 2026-04-22T09:00:00Z\ntext: \"old entry\"\n---\n\n"
        "---\nts: 2026-04-22T11:00:00Z\ntext: \"new entry\"\n---\n",
        encoding="utf-8",
    )
    result = fio.load_raw_since_checkpoint(str(tmp_path))
    assert result == ["new entry"]


def test_load_raw_since_checkpoint_all_old_returns_empty(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "<!-- checkpoint: 2026-04-22T20:00:00Z -->\n\n"
        "---\nts: 2026-04-22T11:00:00Z\ntext: \"old entry\"\n---\n",
        encoding="utf-8",
    )
    assert fio.load_raw_since_checkpoint(str(tmp_path)) == []


def test_load_raw_since_checkpoint_no_file_returns_empty(tmp_path):
    assert fio.load_raw_since_checkpoint(str(tmp_path)) == []


def test_load_raw_since_checkpoint_no_checkpoint_header_returns_all(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "---\nts: 2026-04-22T11:00:00Z\ntext: \"entry\"\n---\n",
        encoding="utf-8",
    )
    result = fio.load_raw_since_checkpoint(str(tmp_path))
    assert result == ["entry"]


# --- append_raw_entry ---

def test_append_raw_entry_creates_file_with_header(tmp_path):
    fio.append_raw_entry(str(tmp_path), "bias quote")
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    assert raw.exists()
    content = raw.read_text(encoding="utf-8")
    assert "<!-- checkpoint:" in content
    assert 'text: "bias quote"' in content
    assert "ts:" in content


def test_append_raw_entry_appends_to_existing(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text("<!-- checkpoint: 2026-04-22T10:00:00Z -->\n", encoding="utf-8")
    fio.append_raw_entry(str(tmp_path), "first")
    fio.append_raw_entry(str(tmp_path), "second")
    content = raw.read_text(encoding="utf-8")
    assert '"first"' in content
    assert '"second"' in content


def test_append_and_load_preserves_text_with_quotes(tmp_path):
    fio.append_raw_entry(str(tmp_path), 'He said "use this instead"')
    result = fio.load_raw_since_checkpoint(str(tmp_path))
    assert result == ['He said "use this instead"']


def test_first_entry_on_new_file_is_not_excluded(tmp_path):
    fio.append_raw_entry(str(tmp_path), "first entry")
    result = fio.load_raw_since_checkpoint(str(tmp_path))
    assert result == ["first entry"]


def test_append_raw_entry_ignores_empty_text(tmp_path):
    fio.append_raw_entry(str(tmp_path), "")
    result = fio.load_raw_since_checkpoint(str(tmp_path))
    assert result == []


# --- reset_raw_md ---

def test_reset_raw_md_clears_entries(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "<!-- checkpoint: 2026-04-22T10:00:00Z -->\n\n"
        "---\nts: 2026-04-22T11:00:00Z\ntext: \"entry\"\n---\n",
        encoding="utf-8",
    )
    fio.reset_raw_md(str(tmp_path))
    content = raw.read_text(encoding="utf-8")
    assert "<!-- checkpoint:" in content
    assert "ts:" not in content
    assert "entry" not in content


def test_reset_raw_md_updates_checkpoint_timestamp(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text("<!-- checkpoint: 2000-01-01T00:00:00Z -->\n", encoding="utf-8")
    fio.reset_raw_md(str(tmp_path))
    content = raw.read_text(encoding="utf-8")
    assert "2000-01-01T00:00:00Z" not in content


# --- load_feedback_rules ---

def test_load_feedback_rules_returns_content(tmp_path):
    rules = tmp_path / ".claude" / "feedback" / "rules.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("<!-- auto-generated -->\n\n- rule one", encoding="utf-8")
    assert fio.load_feedback_rules(str(tmp_path)) == "<!-- auto-generated -->\n\n- rule one"


def test_load_feedback_rules_no_file_returns_empty(tmp_path):
    assert fio.load_feedback_rules(str(tmp_path)) == ""
