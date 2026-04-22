import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import inject_debiasing as ssh


def test_session_start_injects_debiasing():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc123", "cwd": "/tmp"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context
    assert "SUSPEND" in context
    assert "ENUMERATE" in context
    assert "MULTI-AXIS" in context
    assert "VERIFY" in context


def test_session_start_hook_event_name():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc123", "cwd": "/tmp"})
    output = json.loads(f.getvalue())
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_session_start_always_outputs_with_minimal_payload():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": "/tmp"})
    output = json.loads(f.getvalue())
    assert "<cognitive-debiasing>" in output["hookSpecificOutput"]["additionalContext"]


def test_session_start_invalid_payload_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload("not a dict")
    assert f.getvalue() == ""


def test_session_start_injects_rules_when_file_exists(tmp_path):
    rules = tmp_path / ".claude" / "feedback" / "rules.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("- rule one [2026-04-22]", encoding="utf-8")
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "rule one" in context
    assert "<feedback-rules>" in context


def test_session_start_skips_rules_when_no_file(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<feedback-rules>" not in context


def test_session_start_still_injects_core_debiasing_with_rules(tmp_path):
    rules = tmp_path / ".claude" / "feedback" / "rules.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("- rule one", encoding="utf-8")
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc", "cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<cognitive-debiasing>" in context
    assert "COUNTER" in context
    assert "rule one" in context


def test_session_start_contains_seven_step_debiasing():
    import re
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"session_id": "abc", "cwd": "/tmp"})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    steps = re.findall(r'^\d+\.', context, re.MULTILINE)
    assert len(steps) == 7
