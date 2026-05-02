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
    assert stop["hooks"][0]["timeout"] == 210
    assert stop["hooks"][0]["statusMessage"]

    post_tool_use = hooks["PostToolUse"][0]
    assert post_tool_use["matcher"] == "Bash|apply_patch|mcp.*"
    assert post_tool_use["hooks"][0]["type"] == "command"
    assert post_tool_use["hooks"][0]["timeout"] == 30
    assert post_tool_use["hooks"][0]["statusMessage"]


def test_hook_commands_use_plugin_root_substitution_not_session_cwd_or_cache_scan():
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
        assert "${PLUGIN_ROOT}" in command
        assert "/hooks/" in command
        assert "find " not in command
        assert "$HOME/.codex/plugins/cache" not in command


def test_stop_missing_transcript_outputs_valid_noop_json_without_decision():
    hook = PLUGIN / "hooks" / "stop.py"
    payload = {"hook_event_name": "Stop", "cwd": str(PLUGIN)}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    assert output == {}
    assert "decision" not in output


def test_post_tool_use_noop_outputs_nothing():
    hook = PLUGIN / "hooks" / "post_tool_use.py"
    payload = {"hook_event_name": "PostToolUse", "cwd": str(PLUGIN), "tool_name": "Bash"}
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == ""


def test_stop_internal_narration_timeout_is_shorter_than_hook_timeout():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    stop_timeout = hooks["Stop"][0]["hooks"][0]["timeout"]
    stop_source = (PLUGIN / "hooks" / "stop.py").read_text()

    assert "timeout=150" in stop_source
    assert stop_timeout > 150
