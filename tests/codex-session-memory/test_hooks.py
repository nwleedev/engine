import json
import subprocess
import sys
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"


def test_manifest_declares_hooks():
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())
    assert manifest["hooks"] == "./hooks/hooks.json"


def test_session_start_clear_outputs_empty_context():
    hook = PLUGIN / "hooks" / "session_start.py"
    payload = {"hook_event_name": "SessionStart", "source": "clear", "cwd": str(PLUGIN), "session_id": "abc"}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""


def test_hooks_json_contains_session_start_stop_and_post_tool_use():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    event_names = {entry["event"] for entry in hooks["hooks"]}
    assert {"SessionStart", "Stop", "PostToolUse"} <= event_names


def test_stop_outputs_approval_when_payload_is_incomplete():
    hook = PLUGIN / "hooks" / "stop.py"
    payload = {"hook_event_name": "Stop", "cwd": str(PLUGIN)}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == {"decision": "approve"}


def test_post_tool_use_outputs_approval():
    hook = PLUGIN / "hooks" / "post_tool_use.py"
    payload = {"hook_event_name": "PostToolUse", "cwd": str(PLUGIN), "tool_name": "Bash"}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == {"decision": "approve"}
