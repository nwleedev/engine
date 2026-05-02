import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
CHECKPOINT = PLUGIN / "skills" / "checkpoint" / "checkpoint.py"


def load_checkpoint():
    module_name = "test_codex_session_memory_checkpoint"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, CHECKPOINT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_checkpoint_uses_project_local_temp_file(monkeypatch, tmp_path):
    checkpoint = load_checkpoint()
    transcript = tmp_path / "rollout.jsonl"
    transcript.write_text("", encoding="utf-8")
    captured = {}

    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "abc")
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", lambda root, cwd: None)
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: transcript)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id: tmp_path / ".codex" / "sessions" / thread_id)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([{"role": "user", "text": "checkpoint"}], 10))
    monkeypatch.setattr(checkpoint.narrate, "build_prompt", lambda delta: "prompt")

    def fake_call_codex_exec(*, prompt, schema_path, out_path, **kwargs):
        captured["out_path"] = Path(out_path)
        Path(out_path).write_text("{}", encoding="utf-8")
        return {"title": "t", "what_why": "w", "decisions": [], "open": [], "next": "n"}

    monkeypatch.setattr(checkpoint.narrate, "call_codex_exec", fake_call_codex_exec)
    monkeypatch.setattr(checkpoint.narrate, "validate", lambda result: None)
    monkeypatch.setattr(
        checkpoint.context_writer,
        "write_context",
        lambda **kwargs: SimpleNamespace(context_path=tmp_path / ".codex" / "sessions" / "abc" / "contexts" / "ctx.md"),
    )

    assert checkpoint.main() == 0

    expected_temp_dir = tmp_path / "temps" / "2026-05-02" / "codex-session-memory-checkpoint"
    assert captured["out_path"].parent == expected_temp_dir
    assert not captured["out_path"].exists()
