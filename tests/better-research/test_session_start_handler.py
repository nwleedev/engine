import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"

_spec = importlib.util.spec_from_file_location(
    "better_research.session_start_handler", SCRIPTS_DIR / "session_start_handler.py"
)
assert _spec is not None and _spec.loader is not None
ssh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ssh)


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
