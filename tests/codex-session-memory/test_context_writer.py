import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"
CLAUDE_SCRIPTS = ROOT / "plugins" / "session-memory" / "scripts"


def load_writer():
    for name in ("evidence_extractor", "index_io", "session_locator"):
        sys.modules.pop(f"_codex_session_memory_{name}", None)
    spec = importlib.util.spec_from_file_location("context_writer", SCRIPTS / "context_writer.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def narration(title="Policy Update"):
    return {
        "title": title,
        "what_why": "자동 저장 정책을 분리했다.",
        "decisions": ["저장량과 주입량을 분리한다."],
        "open": ["hook fixture 검증이 남았다."],
        "next": "resume handoff를 구현한다.",
    }


def test_writer_creates_context_and_updates_index(tmp_path):
    writer = load_writer()
    result = writer.write_context(
        project_root=tmp_path,
        thread_id="thread-123",
        cwd=str(tmp_path),
        jsonl_path=str(tmp_path / "rollout.jsonl"),
        new_offset=100,
        delta=[{"role": "user", "text": "Please update plugins/codex-session-memory/scripts/policy.py"}],
        narration=narration(),
        reason="force",
    )
    assert result.context_path.exists()
    text = result.context_path.read_text()
    assert "## Evidence" in text
    assert "plugins/codex-session-memory/scripts/policy.py" in text
    index_path = tmp_path / ".codex" / "sessions" / "thread-123" / "INDEX.md"
    assert index_path.exists()
    index_text = index_path.read_text()
    assert "last_processed_offset: 100" in index_text
    assert f"- [{result.context_path.name}] — 자동 저장 정책을 분리했다." in index_text


def test_writer_uses_codex_sibling_modules_when_index_io_is_preloaded(tmp_path):
    spec = importlib.util.spec_from_file_location("index_io", CLAUDE_SCRIPTS / "index_io.py")
    claude_index_io = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    original = sys.modules.get("index_io")
    sys.modules["index_io"] = claude_index_io
    try:
        spec.loader.exec_module(claude_index_io)
        writer = load_writer()
        result = writer.write_context(
            project_root=tmp_path,
            thread_id="thread-123",
            cwd=str(tmp_path),
            jsonl_path=str(tmp_path / "rollout.jsonl"),
            new_offset=100,
            delta=[],
            narration=narration(),
            reason="force",
        )
    finally:
        if original is None:
            sys.modules.pop("index_io", None)
        else:
            sys.modules["index_io"] = original

    assert result.context_path.exists()
    assert result.index_path.exists()
    assert Path(writer.index_io.__file__).resolve() == (SCRIPTS / "index_io.py").resolve()
    assert "last_processed_offset: 100" in result.index_path.read_text()


def test_writer_uses_collision_safe_context_filenames(tmp_path):
    writer = load_writer()
    first = writer.write_context(
        project_root=tmp_path,
        thread_id="thread-123",
        cwd=str(tmp_path),
        jsonl_path=str(tmp_path / "rollout.jsonl"),
        new_offset=100,
        delta=[],
        narration=narration("Repeated Title"),
        reason="force",
    )
    second = writer.write_context(
        project_root=tmp_path,
        thread_id="thread-123",
        cwd=str(tmp_path),
        jsonl_path=str(tmp_path / "rollout.jsonl"),
        new_offset=200,
        delta=[],
        narration=narration("Repeated Title"),
        reason="force",
    )

    assert first.context_path != second.context_path
    assert second.context_path.name == f"{first.context_path.stem}-2{first.context_path.suffix}"
    assert first.context_path.exists()
    assert second.context_path.exists()
    index_text = second.index_path.read_text()
    assert f"- [{first.context_path.name}] — 자동 저장 정책을 분리했다." in index_text
    assert f"- [{second.context_path.name}] — 자동 저장 정책을 분리했다." in index_text
    assert "last_processed_offset: 200" in index_text
