import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-builder/scripts"

_spec = importlib.util.spec_from_file_location(
    "harness_builder.session_start_handler", SCRIPTS_DIR / "session_start_handler.py"
)
assert _spec is not None and _spec.loader is not None
ssh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ssh)


def test_no_harness_injects_setup_reminder(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "harness-setup" in context


def test_hook_event_name_is_session_start(tmp_path):
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_harness_present_injects_content(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    harness_dir.mkdir(parents=True)
    (harness_dir / "nextjs-typescript.md").write_text(
        "---\ndomain: nextjs-typescript\n---\n\n# Harness\n\n## Purpose\nTest.\n"
    )
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "nextjs-typescript" in context


def test_harness_present_injects_active_standards_header(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    harness_dir.mkdir(parents=True)
    (harness_dir / "test.md").write_text("---\ndomain: test\n---\n\n# Test\n")
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "Active Harness Standards" in context


def test_empty_harness_dir_injects_setup_reminder(tmp_path):
    (tmp_path / ".claude" / "harness").mkdir(parents=True)
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({"cwd": str(tmp_path)})
    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "harness-setup" in context


def test_invalid_payload_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload("not-a-dict")
    assert f.getvalue() == ""


def test_missing_cwd_uses_getcwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = io.StringIO()
    with redirect_stdout(f):
        ssh.main_with_payload({})
    output = json.loads(f.getvalue())
    assert "hookSpecificOutput" in output
