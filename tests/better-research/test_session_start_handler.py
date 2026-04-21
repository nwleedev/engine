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
        ssh.main_with_payload({"session_id": "abc123"})
    output = json.loads(f.getvalue())
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_session_start_always_outputs_regardless_of_payload():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({})
    output = json.loads(f.getvalue())
    assert "<cognitive-debiasing>" in output["hookSpecificOutput"]["additionalContext"]


def test_session_start_invalid_payload_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload("not a dict")
    assert f.getvalue() == ""
