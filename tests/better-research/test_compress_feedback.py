import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import compress_feedback as cf


# --- build_compression_prompt ---

def test_build_compression_prompt_includes_entries():
    result = cf.build_compression_prompt(["quote one", "quote two"], "")
    assert '"quote one"' in result
    assert '"quote two"' in result


def test_build_compression_prompt_includes_existing_rules():
    result = cf.build_compression_prompt(["quote"], "- existing rule")
    assert "existing rule" in result


def test_build_compression_prompt_empty_rules_shows_none():
    result = cf.build_compression_prompt(["quote"], "")
    assert "(없음)" in result


# --- parse_rules_from_result ---

def test_parse_rules_from_result_extracts_list():
    raw = '{"rules": ["rule one [2026-04-22]", "rule two [2026-04-22]"]}'
    result = cf.parse_rules_from_result(raw)
    assert result == ["rule one [2026-04-22]", "rule two [2026-04-22]"]


def test_parse_rules_from_result_handles_preamble():
    raw = 'Some preamble text.\n{"rules": ["rule one"]}'
    result = cf.parse_rules_from_result(raw)
    assert result == ["rule one"]


def test_parse_rules_from_result_invalid_json_returns_none():
    assert cf.parse_rules_from_result("not json") is None


def test_parse_rules_from_result_missing_rules_key_returns_none():
    assert cf.parse_rules_from_result('{"other": []}') is None


# --- write_rules_md ---

def test_write_rules_md_creates_file(tmp_path):
    cf.write_rules_md(str(tmp_path), ["rule one [2026-04-22]", "rule two [2026-04-22]"], source_count=2)
    path = tmp_path / ".claude" / "feedback" / "rules.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "<!-- auto-generated" in content
    assert "rule one" in content
    assert "rule two" in content
    assert "source-entries: 2" in content


def test_write_rules_md_overwrites_existing(tmp_path):
    path = tmp_path / ".claude" / "feedback" / "rules.md"
    path.parent.mkdir(parents=True)
    path.write_text("old content", encoding="utf-8")
    cf.write_rules_md(str(tmp_path), ["new rule"], source_count=1)
    assert "old content" not in path.read_text(encoding="utf-8")


# --- run_compression (integration with mocked claude -p) ---

def test_run_compression_calls_claude_p_and_updates_files(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "<!-- checkpoint: 2000-01-01T00:00:00Z -->\n\n"
        '---\nts: 2026-04-22T10:00:00Z\ntext: "bias quote"\n---\n',
        encoding="utf-8",
    )
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"result": "{\\"rules\\": [\\"new rule [2026-04-22]\\"]}"}'
    with patch("subprocess.run", return_value=mock_result):
        cf.run_compression(str(tmp_path))
    rules = tmp_path / ".claude" / "feedback" / "rules.md"
    assert rules.exists()
    assert "new rule" in rules.read_text(encoding="utf-8")
    # raw.md should be reset (no ts: entries)
    assert "ts:" not in raw.read_text(encoding="utf-8")


def test_run_compression_skips_when_no_new_entries(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text("<!-- checkpoint: 2099-01-01T00:00:00Z -->\n", encoding="utf-8")
    with patch("subprocess.run") as mock_sub:
        cf.run_compression(str(tmp_path))
    mock_sub.assert_not_called()


def test_run_compression_leaves_raw_unchanged_on_claude_failure(tmp_path):
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    original = (
        "<!-- checkpoint: 2000-01-01T00:00:00Z -->\n\n"
        '---\nts: 2026-04-22T10:00:00Z\ntext: "quote"\n---\n'
    )
    raw.write_text(original, encoding="utf-8")
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error"
    with patch("subprocess.run", return_value=mock_result):
        cf.run_compression(str(tmp_path))
    assert raw.read_text(encoding="utf-8") == original
