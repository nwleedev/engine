# tests/quality-guard/test_user_prompt_handler.py
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import ref_index_reader as rir


# --- ref_index_reader ---

def test_read_index_returns_content_when_exists(tmp_path):
    index = tmp_path / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True)
    index.write_text("| Python Typing | .claude/refs/python/typing.md | python |", encoding="utf-8")
    result = rir.read_index(str(tmp_path))
    assert "Python Typing" in result


def test_read_index_returns_empty_when_absent(tmp_path):
    result = rir.read_index(str(tmp_path))
    assert result == ""


def test_read_index_returns_empty_on_read_error(tmp_path):
    index = tmp_path / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True)
    index.write_bytes(b"\xff\xfe")  # invalid UTF-8 sequence
    result = rir.read_index(str(tmp_path))
    assert result == ""


# --- user_prompt_submit hook behaviour ---
# Import the handler module (not the hook shim)
sys.path.insert(0, str(SCRIPTS_DIR))
import user_prompt_handler as uph


def test_user_prompt_no_refs_injects_debiasing_fallback(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "Implement feature X", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context


def test_user_prompt_with_refs_injects_quality_instruction(tmp_path):
    index = tmp_path / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True)
    index.write_text("| Python Docs | .claude/refs/python/docs.md | python |", encoding="utf-8")
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "Write a Python function", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<quality-instruction>" in context


def test_user_prompt_with_refs_includes_ref_reminder(tmp_path):
    index = tmp_path / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True)
    index.write_text("| Clean Code | .claude/refs/general/clean-code.md | patterns |", encoding="utf-8")
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "Refactor this class", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "Read tool" in context or "read the ref file" in context


def test_user_prompt_empty_prompt_produces_no_output(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "", "cwd": str(tmp_path)})
    assert f.getvalue() == ""


def test_user_prompt_non_dict_payload_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload("not a dict")
    assert f.getvalue() == ""


def test_user_prompt_hook_event_name(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "hello", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
