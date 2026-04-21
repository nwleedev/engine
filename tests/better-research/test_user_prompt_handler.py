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


# --- main_with_payload: D path ---

def test_d_path_injects_perspectives(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "validity,cross_check")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "normal question"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "validity" in context
    assert "cross_check" in context

def test_d_path_empty_env_no_output(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "normal question"})
    assert f.getvalue() == ""


# --- main_with_payload: C path ---

def test_c_path_injects_skill_content(monkeypatch):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "analyze this /q"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "Research Protocol" in context
    assert "Root Cause" in context

def test_c_path_missing_skill_file_no_output(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "analyze this /q"})
    assert f.getvalue() == ""


# --- main_with_payload: D + C combined ---

def test_d_and_c_both_inject(monkeypatch):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "validity,root_cause_solution")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "why is this slow /q"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "validity" in context
    assert "Research Protocol" in context
    assert "\n\n---\n\n" in context


# --- edge cases ---

def test_empty_prompt_no_output(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_PERSPECTIVES", "validity")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": ""})
    assert f.getvalue() == ""

def test_marker_only_prompt_no_output(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "/q"})
    assert f.getvalue() == ""


# --- Layer 1b: anti-frame-bias on design keywords ---

def test_layer1b_injects_debiasing_on_korean_keyword(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "어떻게 설계할까요?"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context
    assert "SUSPEND" in context

def test_layer1b_injects_debiasing_on_english_keyword(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "what approach should we take?"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context

def test_layer1b_no_injection_without_keyword(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "what is the capital of France?"})
    assert f.getvalue() == ""

def test_layer1b_and_layer2_both_inject_on_keyword_plus_marker(monkeypatch):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(PLUGIN_ROOT))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "설계 방법을 알려줘 /q"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context
    assert "Research Protocol" in context
    assert "\n\n---\n\n" in context

def test_layer1b_only_debiasing_when_keyword_no_marker(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_PERSPECTIVES", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "구현 방식 논의"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context
    assert "Research Protocol" not in context
