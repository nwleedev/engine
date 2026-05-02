import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_writer():
    spec = importlib.util.spec_from_file_location("context_writer", SCRIPTS / "context_writer.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_writer_creates_context_and_updates_index(tmp_path):
    writer = load_writer()
    result = writer.write_context(
        project_root=tmp_path,
        thread_id="thread-123",
        cwd=str(tmp_path),
        jsonl_path=str(tmp_path / "rollout.jsonl"),
        new_offset=100,
        delta=[{"role": "user", "text": "Please update plugins/codex-session-memory/scripts/policy.py"}],
        narration={
            "title": "Policy Update",
            "what_why": "자동 저장 정책을 분리했다.",
            "decisions": ["저장량과 주입량을 분리한다."],
            "open": ["hook fixture 검증이 남았다."],
            "next": "SessionStart 주입을 구현한다.",
        },
        reason="force",
    )
    assert result.context_path.exists()
    text = result.context_path.read_text()
    assert "## Evidence" in text
    assert "plugins/codex-session-memory/scripts/policy.py" in text
    assert (tmp_path / ".codex" / "sessions" / "thread-123" / "INDEX.md").exists()
