import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"
PLUGIN_ROOT = Path(__file__).parent.parent.parent / "plugins/better-research"

sys.path.insert(0, str(SCRIPTS_DIR))
import user_prompt_handler as uph


# --- detect_marker ---

def test_detect_marker_q_at_end():
    assert uph.detect_marker("analyze this /q") is True

def test_detect_marker_q_at_start():
    assert uph.detect_marker("/q analyze this") is True

def test_detect_marker_query():
    assert uph.detect_marker("/query what is this") is True

def test_detect_marker_research_inline():
    assert uph.detect_marker("explain /research this topic") is True

def test_detect_marker_case_insensitive():
    assert uph.detect_marker("analyze /Q this") is True

def test_detect_marker_url_no_match():
    assert uph.detect_marker("see example.com/query for details") is False

def test_detect_marker_path_no_match():
    assert uph.detect_marker("edit src/research/file.py") is False

def test_detect_marker_no_marker():
    assert uph.detect_marker("just a normal question") is False

def test_detect_marker_empty_prompt():
    assert uph.detect_marker("") is False

def test_detect_marker_q_with_trailing_paren():
    assert uph.detect_marker("analyze (/q) why") is True

def test_detect_marker_q_with_trailing_bracket():
    assert uph.detect_marker("see [/q] this") is True


# --- strip_marker ---

def test_strip_marker_removes_q():
    result = uph.strip_marker("analyze this /q")
    assert "/q" not in result.lower()
    assert "analyze this" in result

def test_strip_marker_removes_query_at_start():
    result = uph.strip_marker("/query what is this")
    assert "/query" not in result.lower()
    assert "what is this" in result

def test_strip_marker_removes_research_inline():
    result = uph.strip_marker("explain /research this")
    assert "/research" not in result.lower()
    assert "explain" in result
    assert "this" in result

def test_strip_marker_does_not_alter_url():
    original = "see example.com/query for details"
    result = uph.strip_marker(original)
    assert result == original

def test_strip_marker_no_double_spaces():
    result = uph.strip_marker("analyze /q this topic")
    assert "  " not in result
    assert result == "analyze this topic"


# --- main_with_payload: raw feedback injection ---

def test_injects_raw_entries_when_present(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    raw = tmp_path / ".claude" / "feedback" / "raw.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        "<!-- checkpoint: 2000-01-01T00:00:00Z -->\n\n"
        '---\nts: 2026-04-22T10:00:00Z\ntext: "bias quote here"\n---\n',
        encoding="utf-8",
    )
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "normal question", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "bias quote here" in context
    assert "<session-feedback-observations>" in context


def test_no_output_when_no_raw_entries_and_no_marker(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "normal question", "cwd": str(tmp_path)})
    assert f.getvalue() == ""


def test_does_not_inject_cognitive_debiasing_in_userpromptsubmit(monkeypatch):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "explain /q", "cwd": "/tmp"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" not in context


# --- main_with_payload: research marker ---

def test_research_marker_injects_skill_without_debiasing(monkeypatch):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "analyze /q", "cwd": "/tmp"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "Research Protocol" in context
    assert "<cognitive-debiasing>" not in context


def test_research_marker_missing_skill_file_no_output(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "analyze /q", "cwd": str(tmp_path)})
    assert f.getvalue() == ""


# --- main_with_payload: perspectives ---

def test_perspectives_injected_even_without_marker_or_raw(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "validity,cross_check")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "normal question", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "validity" in context
    assert "cross_check" in context


# --- main_with_payload: combined ---

def test_raw_entries_and_marker_both_injected(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    raw_md = tmp_path / ".claude" / "feedback" / "raw.md"
    raw_md.parent.mkdir(parents=True)
    raw_md.write_text(
        "<!-- checkpoint: 2000-01-01T00:00:00Z -->\n\n"
        '---\nts: 2026-04-22T10:00:00Z\ntext: "observed bias"\n---\n',
        encoding="utf-8",
    )
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "explain /q", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "observed bias" in context
    assert "Research Protocol" in context


# --- edge cases ---

def test_empty_prompt_no_output(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "validity")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "", "cwd": str(tmp_path)})
    assert f.getvalue() == ""
