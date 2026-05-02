import json
import importlib.util
import os
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
INTERNAL_ENV = "CODEX_SESSION_MEMORY_INTERNAL"


def load_hook(script_name: str):
    module_name = f"test_codex_session_memory_{script_name}"
    spec = importlib.util.spec_from_file_location(module_name, PLUGIN / "hooks" / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_script(script_name: str):
    module_name = f"test_codex_session_memory_script_{script_name}"
    spec = importlib.util.spec_from_file_location(module_name, PLUGIN / "scripts" / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


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
        assert command.startswith('python3 "${PLUGIN_ROOT}/hooks/')
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


def test_hook_entrypoints_noop_when_internal_env_is_set():
    env = {**os.environ, INTERNAL_ENV: "1"}
    cases = [
        ("session_start.py", {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(PLUGIN), "session_id": "abc"}, ""),
        ("post_tool_use.py", {"hook_event_name": "PostToolUse", "cwd": str(PLUGIN), "tool_name": "Bash"}, ""),
        ("stop.py", {"hook_event_name": "Stop", "cwd": str(PLUGIN), "session_id": "abc"}, "{}\n"),
    ]

    for script_name, payload, expected_stdout in cases:
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "hooks" / script_name)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        assert result.stdout == expected_stdout


def test_stop_internal_narration_timeout_is_shorter_than_hook_timeout():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
    stop_timeout = hooks["Stop"][0]["hooks"][0]["timeout"]
    stop_source = (PLUGIN / "hooks" / "stop.py").read_text()

    assert "timeout=150" in stop_source
    assert stop_timeout > 150


def test_stop_counts_only_tool_role_text_for_tool_output_threshold():
    stop = load_hook("stop")

    assert stop._tool_output_chars(
        [
            {"role": "assistant", "text": "assistant text that is not tool output"},
            {"role": "tool", "text": "tool output"},
            {"role": "tool", "text": "more"},
        ]
    ) == len("tool output") + len("more")


def test_stop_lock_timeout_fails_open_without_writing(monkeypatch, tmp_path):
    stop = load_hook("stop")
    transcript = tmp_path / "rollout.jsonl"
    transcript.write_text("", encoding="utf-8")
    session_dir = tmp_path / ".codex" / "sessions" / "abc"
    session_dir.mkdir(parents=True)
    (session_dir / ".session-memory.lock").write_text("locked", encoding="utf-8")
    write_calls = []
    narration_calls = []

    def fake_load(filename, module_name):
        if filename == "dotenv_loader.py":
            return SimpleNamespace(load_project_dotenv=lambda cwd: None)
        if filename == "project_root.py":
            return SimpleNamespace(
                find_project_root=lambda cwd: str(tmp_path),
                assert_root_is_canonical=lambda root, cwd: None,
            )
        if filename == "session_locator.py":
            return SimpleNamespace(
                find_jsonl_by_thread=lambda thread_id: transcript,
                data_session_dir=lambda root, thread_id: session_dir,
            )
        if filename == "index_io.py":
            return SimpleNamespace(read_frontmatter=lambda path: {"last_processed_offset": 0})
        if filename == "jsonl_parser.py":
            return SimpleNamespace(extract_delta=lambda path, offset: ([{"role": "user", "text": "x" * 5000}], 10))
        if filename == "policy.py":
            return SimpleNamespace(should_save=lambda **kwargs: SimpleNamespace(save=True, reason="test"))
        if filename == "narrate.py":
            return SimpleNamespace(
                build_prompt=lambda delta: "prompt",
                call_codex_exec=lambda **kwargs: narration_calls.append(kwargs)
                or {"title": "t", "what_why": "w", "decisions": [], "open": [], "next": "n"},
                validate=lambda result: None,
            )
        if filename == "context_writer.py":
            return SimpleNamespace(write_context=lambda **kwargs: write_calls.append(kwargs))
        if filename == "lockfile.py":
            return load_script("lockfile")
        raise AssertionError(filename)

    monkeypatch.setattr(stop, "_load_script_module", fake_load)

    stop._save({"cwd": str(tmp_path), "session_id": "abc", "transcript_path": str(transcript)})

    assert narration_calls == []
    assert write_calls == []


def test_stop_refuses_to_write_when_root_is_not_canonical(monkeypatch, tmp_path):
    stop = load_hook("stop")
    write_calls = []

    def fake_load(filename, module_name):
        if filename == "dotenv_loader.py":
            return SimpleNamespace(load_project_dotenv=lambda cwd: None)
        if filename == "project_root.py":
            return SimpleNamespace(
                find_project_root=lambda cwd: str(tmp_path),
                assert_root_is_canonical=lambda root, cwd: (_ for _ in ()).throw(RuntimeError("not canonical")),
            )
        if filename == "session_locator.py":
            return SimpleNamespace(find_jsonl_by_thread=lambda thread_id: (_ for _ in ()).throw(AssertionError("should not find transcript")))
        if filename == "context_writer.py":
            return SimpleNamespace(write_context=lambda **kwargs: write_calls.append(kwargs))
        return SimpleNamespace()

    monkeypatch.setattr(stop, "_load_script_module", fake_load)

    stop._save({"cwd": str(tmp_path), "session_id": "abc"})

    assert write_calls == []


def test_stop_passes_reentry_env_into_narration(monkeypatch, tmp_path):
    stop = load_hook("stop")
    transcript = tmp_path / "rollout.jsonl"
    transcript.write_text("")
    captured = {}

    def fake_call_codex_exec(**kwargs):
        captured.update(kwargs)
        return {"title": "t", "what_why": "w", "decisions": [], "open": [], "next": "n"}

    def fake_load(filename, module_name):
        if filename == "dotenv_loader.py":
            return SimpleNamespace(load_project_dotenv=lambda cwd: None)
        if filename == "project_root.py":
            return SimpleNamespace(
                find_project_root=lambda cwd: str(tmp_path),
                assert_root_is_canonical=lambda root, cwd: None,
            )
        if filename == "session_locator.py":
            return SimpleNamespace(
                find_jsonl_by_thread=lambda thread_id: transcript,
                data_session_dir=lambda root, thread_id: tmp_path / ".codex" / "sessions" / thread_id,
            )
        if filename == "index_io.py":
            return SimpleNamespace(read_frontmatter=lambda path: {"last_processed_offset": 0})
        if filename == "jsonl_parser.py":
            return SimpleNamespace(extract_delta=lambda path, offset: ([{"role": "user", "text": "x" * 5000}], 10))
        if filename == "policy.py":
            return SimpleNamespace(should_save=lambda **kwargs: SimpleNamespace(save=True, reason="test"))
        if filename == "narrate.py":
            return SimpleNamespace(
                build_prompt=lambda delta: "prompt",
                call_codex_exec=fake_call_codex_exec,
                validate=lambda result: None,
            )
        if filename == "context_writer.py":
            return SimpleNamespace(write_context=lambda **kwargs: None)
        if filename == "lockfile.py":
            return load_script("lockfile")
        raise AssertionError(filename)

    monkeypatch.setattr(stop, "_load_script_module", fake_load)

    stop._save({"cwd": str(tmp_path), "session_id": "abc", "transcript_path": str(transcript)})

    assert captured["env"][INTERNAL_ENV] == "1"
    assert captured["timeout"] == 150


def test_narrate_passes_env_to_subprocess(monkeypatch, tmp_path):
    narrate = load_script("narrate")
    captured = {}
    out_path = tmp_path / "out.json"

    def fake_run(cmd, capture_output, text, timeout, env):
        captured["env"] = env
        out_path.write_text(json.dumps({"title": "t", "what_why": "w", "decisions": [], "open": [], "next": "n"}))
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(narrate.subprocess, "run", fake_run)

    narrate.call_codex_exec(
        prompt="prompt",
        schema_path=tmp_path / "schema.json",
        out_path=out_path,
        timeout=150,
        env={INTERNAL_ENV: "1"},
    )

    assert captured["env"] == {INTERNAL_ENV: "1"}
