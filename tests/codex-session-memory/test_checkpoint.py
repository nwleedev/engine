import importlib.util
import json
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
    monkeypatch.delenv("CODEX_SESSION_PARENT_ID", raising=False)
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


def write_child_session_meta(jsonl: Path, *, parent_thread_id: str | None):
    thread_spawn = {}
    if parent_thread_id is not None:
        thread_spawn["parent_thread_id"] = parent_thread_id
    jsonl.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "source": {
                        "subagent": {
                            "thread_spawn": thread_spawn,
                        },
                    },
                },
            }
        )
        + "\n",
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


def test_prepare_uses_hh00_context_path_and_reuses_existing_file(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    session_dir = tmp_path / ".codex" / "sessions" / "test-thread"
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    existing = contexts_dir / "CONTEXT-20260503-1500-checkpoint.md"
    existing.write_text("# Existing\n", encoding="utf-8")

    class FakeDatetime:
        @classmethod
        def now(cls):
            return cls()

        def strftime(self, fmt):
            assert fmt == "%Y%m%d-%H00"
            return "20260503-1500"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint, "datetime", FakeDatetime)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id, role="main": session_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert f"context_path: {existing}" in output
    assert existing.read_text(encoding="utf-8") == "# Existing\n"


def test_prepare_child_without_parent_uses_auto_resolution(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    write_child_session_meta(jsonl, parent_thread_id="parent-thread")
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id, role="main": child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output


def test_prepare_parent_without_role_is_child_intent(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id, role="main": child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--parent", "parent-thread"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output


def test_prepare_uses_env_parent_as_child_intent(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_PARENT_ID", "env-parent-thread")
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id, role="main": child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: env-parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output


def test_prepare_fails_when_main_role_conflicts_with_env_parent(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_PARENT_ID", "env-parent-thread")
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)

    assert checkpoint.main(["prepare", "--role", "main"]) == 2

    captured = capsys.readouterr()
    assert "conflicts" in captured.err
    assert "role: main" not in captured.out


def test_prepare_fails_when_main_role_conflicts_with_child_metadata(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    write_child_session_meta(jsonl, parent_thread_id="parent-thread")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)

    assert checkpoint.main(["prepare", "--role", "main"]) == 2

    captured = capsys.readouterr()
    assert "conflicts" in captured.err
    assert "role: main" not in captured.out


def test_prepare_fails_when_child_detected_without_parent(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    write_child_session_meta(jsonl, parent_thread_id=None)

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)

    assert checkpoint.main(["prepare", "--role", "child"]) == 2

    captured = capsys.readouterr()
    assert "parent" in captured.err
    assert "retry" in captured.err
    assert "role: main" not in captured.out


def test_prepare_checks_parent_resolution_before_jsonl_missing_failure(
    monkeypatch, tmp_path, capsys
):
    checkpoint = load_checkpoint()
    calls = []

    def resolve_parent_thread_id(*, thread_id, rollout_path):
        calls.append((thread_id, rollout_path))
        return checkpoint.pl.ParentResolution(
            role="child",
            parent_thread_id="parent-thread",
            source="state_db_thread_spawn_edges",
            confidence="high",
        )

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(checkpoint.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert checkpoint.main(["prepare"]) == 2

    captured = capsys.readouterr()
    assert calls == [("child-thread", None)]
    assert "no rollout JSONL" in captured.err
    assert "role: main" not in captured.out


def test_prepare_invalid_role_prints_specific_error(capsys):
    checkpoint = load_checkpoint()

    assert checkpoint.main(["prepare", "--role", "nope"]) == 2

    assert "--role must be main or child" in capsys.readouterr().err


def test_prepare_unknown_argument_prints_specific_error(capsys):
    checkpoint = load_checkpoint()

    assert checkpoint.main(["prepare", "--bogus"]) == 2

    assert "unknown prepare argument" in capsys.readouterr().err


def test_prepare_child_outputs_hidden_child_target_and_parent_link(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "data_session_dir", lambda root, thread_id, role="main": child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child", "--parent", "parent-thread"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output
    assert f"parent_index_path: {tmp_path / '.codex' / 'sessions' / 'parent-thread' / 'INDEX.md'}" in output
    assert "parent_child_entry:" in output


def test_verify_requires_sections_and_index_entry(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## 컨텍스트 목록\n\n- [{context.name}] - test\n", encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 0
    assert "verify: ok" in capsys.readouterr().out


def test_verify_accepts_hidden_child_session_context(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = (
        tmp_path
        / ".codex"
        / "sessions"
        / "_children"
        / "child-thread"
        / "contexts"
        / "CONTEXT-20260503-1500-checkpoint.md"
    )
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(
        "---\nrole: child\nparent_session_id: parent-thread\n---\n\n"
        f"## 컨텍스트 목록\n\n- [{context.name}] - child checkpoint\n",
        encoding="utf-8",
    )

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
