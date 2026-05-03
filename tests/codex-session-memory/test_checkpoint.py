import importlib.util
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
CHECKPOINT = PLUGIN / "skills" / "checkpoint" / "checkpoint.py"


def load_checkpoint():
    spec = importlib.util.spec_from_file_location("checkpoint_skill", CHECKPOINT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_prepare_outputs_context_target_and_evidence(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", lambda root, cwd: None)
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id: tmp_path / ".codex" / "sessions" / thread_id)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([{"role": "assistant", "text": "Run `git status --short`"}], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "thread_id: test-thread" in output
    assert "context_path:" in output
    assert "INDEX.md" in output
    assert "git status --short" in output
    assert "## [현재 상태 (Phase)]" in output


def test_verify_requires_sections_and_index_entry(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text(
        "# test\n\n"
        "## [현재 상태 (Phase)]\nDone\n\n"
        "## [문제 및 아키텍처 결정 (ADR)]\nDecision\n\n"
        "## [도구 및 파일 변경 내역]\nFiles\n\n"
        "## [검증 결과]\nTests\n\n"
        "## [남은 위험 및 미해결 사항]\nNone\n\n"
        "## [다음 단계 (Next Steps)]\n- [ ] Next\n",
        encoding="utf-8",
    )
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## 컨텍스트 목록\n\n- [{context.name}] - test\n", encoding="utf-8")

    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))

    assert checkpoint.main(["verify", str(context)]) == 0
    assert "verify: ok" in capsys.readouterr().out


def test_verify_fails_when_required_section_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text("# test\n", encoding="utf-8")
    (context.parent.parent / "INDEX.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "missing section" in capsys.readouterr().err
