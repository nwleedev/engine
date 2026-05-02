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
    assert {"SessionStart", "Stop", "PostToolUse"} <= set(hooks["hooks"])


def test_hooks_json_uses_official_nested_command_shape():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]

    session_start = hooks["SessionStart"][0]
    assert session_start["matcher"] == "startup|resume"
    assert session_start["hooks"][0]["type"] == "command"
    assert session_start["hooks"][0]["timeout"] == 30
    assert session_start["hooks"][0]["statusMessage"]

    stop = hooks["Stop"][0]
    assert "matcher" not in stop
    assert stop["hooks"][0]["type"] == "command"
    assert stop["hooks"][0]["timeout"] == 180
    assert stop["hooks"][0]["statusMessage"]

    post_tool_use = hooks["PostToolUse"][0]
    assert post_tool_use["matcher"] == "Bash|apply_patch|mcp.*"
    assert post_tool_use["hooks"][0]["type"] == "command"
    assert post_tool_use["hooks"][0]["timeout"] == 30
    assert post_tool_use["hooks"][0]["statusMessage"]


def test_hook_commands_resolve_from_installed_plugin_cache_not_session_cwd():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    commands = [
        handler["command"]
        for groups in hooks.values()
        for group in groups
        for handler in group["hooks"]
    ]

    assert commands
    for command in commands:
        assert not command.startswith("python3 hooks/")
        assert "codex-session-memory" in command
        assert "/hooks/" in command
        assert "$HOME/.codex/plugins/cache" in command


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
