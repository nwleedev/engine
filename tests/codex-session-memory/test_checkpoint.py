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


def patch_project(monkeypatch, checkpoint, tmp_path):
    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", lambda root, cwd: None)


def write_valid_context(context: Path):
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


def test_prepare_outputs_context_target_and_evidence(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
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
    assert "index_entry: -" in output
    assert "last_processed_offset: 10" in output


def test_verify_requires_sections_and_index_entry(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## 컨텍스트 목록\n\n- [{context.name}] - test\n", encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 0
    assert "verify: ok" in capsys.readouterr().out


def test_verify_fails_when_required_section_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text("# test\n", encoding="utf-8")
    (context.parent.parent / "INDEX.md").write_text("", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "missing section" in capsys.readouterr().err


def test_prepare_fails_when_thread_id_missing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: None)

    assert checkpoint.main(["prepare"]) == 2
    assert "CODEX_THREAD_ID" in capsys.readouterr().err


def test_prepare_fails_when_jsonl_missing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: None)

    assert checkpoint.main(["prepare"]) == 2
    assert "no rollout JSONL" in capsys.readouterr().err


def test_unknown_command_prints_usage(capsys):
    checkpoint = load_checkpoint()

    assert checkpoint.main(["unknown"]) == 2
    assert "usage:" in capsys.readouterr().err


def test_verify_fails_when_index_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not exist" in capsys.readouterr().err


def test_verify_fails_when_index_reference_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    (context.parent.parent / "INDEX.md").write_text("## 컨텍스트 목록\n", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not include context entry" in capsys.readouterr().err


def test_verify_rejects_context_path_outside_project_session_tree(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path.parent / "outside-contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "outside project session contexts" in capsys.readouterr().err


def test_verify_rejects_section_substring_false_positive(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text(
        "# test\n\n"
        "Paragraph mentions ## [현재 상태 (Phase)] but is not a heading line.\n\n"
        "## [문제 및 아키텍처 결정 (ADR)]\nDecision\n\n"
        "## [도구 및 파일 변경 내역]\nFiles\n\n"
        "## [검증 결과]\nTests\n\n"
        "## [남은 위험 및 미해결 사항]\nNone\n\n"
        "## [다음 단계 (Next Steps)]\n- [ ] Next\n",
        encoding="utf-8",
    )
    (context.parent.parent / "INDEX.md").write_text(f"- [{context.name}] - test\n", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "missing section" in capsys.readouterr().err


def test_verify_rejects_index_substring_false_positive(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    (context.parent.parent / "INDEX.md").write_text(
        f"The file {context.name} exists but there is no list entry.\n",
        encoding="utf-8",
    )
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not include context entry" in capsys.readouterr().err


def test_prepare_does_not_write_context_or_index(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    session_dir = tmp_path / ".codex" / "sessions" / "test-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 12))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    context_line = next(line for line in output.splitlines() if line.startswith("context_path: "))
    context_path = Path(context_line.removeprefix("context_path: "))
    assert not context_path.exists()
    assert not (session_dir / "INDEX.md").exists()


def test_root_errors_return_clear_stderr(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))

    def fail_root(root, cwd):
        raise RuntimeError("not canonical")

    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", fail_root)

    assert checkpoint.main(["prepare"]) == 2
    assert "not canonical" in capsys.readouterr().err
