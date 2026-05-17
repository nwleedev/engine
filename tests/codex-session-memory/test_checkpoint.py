import ast
import importlib.util
import json
from pathlib import Path
from typing import Optional


PLUGIN = (
    Path(__file__).resolve().parents[2]
    / "plugin-sources"
    / "session-memory"
    / "adapters"
    / "codex"
)
CHECKPOINT = PLUGIN / "skills" / "checkpoint" / "checkpoint.py"


def load_checkpoint():
    spec = importlib.util.spec_from_file_location("checkpoint_skill", CHECKPOINT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def patch_project(monkeypatch, checkpoint, tmp_path):
    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.delenv("CODEX_SESSION_PARENT_ID", raising=False)
    monkeypatch.delenv("CODEX_SESSION_ID", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", lambda root, cwd: None)


def write_valid_context(context: Path):
    context.parent.mkdir(parents=True)
    context.write_text(
        "# test\n\n"
        "## current_goal\nDone\n\n"
        "## executive_summary\nSummary\n\n"
        "## detailed_state\nState\n\n"
        "## decisions\nDecision\n\n"
        "## files\nFiles\n\n"
        "## verification\nTests\n\n"
        "## risks\nNone\n\n"
        "## next_actions\n- [ ] Next\n\n"
        "## graph_context\nGraph\n",
        encoding="utf-8",
    )


REQUIRED_CONTEXT_HEADINGS = (
    "## current_goal",
    "## executive_summary",
    "## detailed_state",
    "## decisions",
    "## files",
    "## verification",
    "## risks",
    "## next_actions",
    "## graph_context",
)


def write_child_session_meta(jsonl: Path, *, parent_thread_id: Optional[str]):
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
    monkeypatch.setenv("CODEX_SESSION_ID", "test-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([{"role": "assistant", "text": "Run `git status --short`"}], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "session_id: test-session" in output
    assert "source_thread_id: test-thread" in output
    assert "context_path:" in output
    assert "INDEX.md" in output
    assert "git status --short" in output
    assert "## current_goal" in output
    assert "index_entry: -" in output
    assert "last_processed_offset: 10" in output


def test_prepare_outputs_handoff_without_writing_context_or_index(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(
        checkpoint.jp,
        "extract_delta",
        lambda path, offset: (
            [
                {
                    "role": "user",
                    "text": (
                        "Fix session-memory so "
                        "plugin-sources/session-memory/adapters/codex/skills/checkpoint/checkpoint.py "
                        "stores actual summaries."
                    ),
                },
                {
                    "role": "assistant",
                    "text": (
                        "Updated tests/codex-session-memory/test_checkpoint.py and ran "
                        "`uv run --isolated --python /usr/local/bin/python3.12 --with pytest pytest "
                        "tests/codex-session-memory/test_checkpoint.py -q`."
                    ),
                },
            ],
            64,
        ),
    )

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    context_line = next(line for line in output.splitlines() if line.startswith("context_path: "))
    context_path = Path(context_line.removeprefix("context_path: "))

    assert "The active Codex must write the context file and update INDEX.md." in output
    assert "## required context template" in output
    assert "## mandatory active Codex actions" in output
    assert "template is a required structure, not a completed artifact" in output
    assert "active Codex's responsibility" in output
    assert "Do not refuse or stop" in output
    assert "# <title>" in output
    assert "guidance:" in output
    assert "plugin-sources/session-memory/adapters/codex/skills/checkpoint/checkpoint.py" in output
    assert "tests/codex-session-memory/test_checkpoint.py" in output
    assert "uv run --isolated --python /usr/local/bin/python3.12 --with pytest pytest" in output
    assert "Do not save the template unchanged." in output
    assert "prepare is not a completed checkpoint" in output
    assert not context_path.exists()
    assert not (context_path.parent.parent / "INDEX.md").exists()


def test_prepare_outputs_flat_artifact_target(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert ".codex/session-memory/threads/test-session/INDEX.md" in output
    assert "_children" not in output
    assert "# <title>" in output
    assert "guidance:" in output
    for heading in REQUIRED_CONTEXT_HEADINGS:
        assert heading in output


def test_prepare_context_path_uses_timestamp_task_id_nonce_and_writes_metadata(
    monkeypatch, tmp_path, capsys
):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-source-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return cls()

        def strftime(self, fmt):
            if fmt == "%Y%m%d-%H%M%S":
                return "20260517-101112"
            if fmt == "%Y-%m-%dT%H:%M:%SZ":
                return "2026-05-17T10:11:12Z"
            raise AssertionError(fmt)

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
    monkeypatch.setattr(checkpoint, "datetime", FakeDatetime)
    monkeypatch.setattr(checkpoint.secrets, "token_hex", lambda n: "abc123")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    expected = (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "target-session"
        / "contexts"
        / "CONTEXT-20260517-101112-checkpoint-abc123.md"
    )
    assert f"context_path: {expected}" in output
    assert not expected.exists()
    assert "session_id: target-session" in output
    assert "source_thread_id: source-thread" in output
    assert "CONTEXT-source-thread" not in expected.name


def test_prepare_mismatch_warns_and_writes_only_to_session_id_path(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-source-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert "CODEX_THREAD_ID" in captured.err
    assert "CODEX_SESSION_ID" in captured.err
    assert ".codex/session-memory/threads/target-session/INDEX.md" in captured.out
    assert ".codex/session-memory/threads/source-thread/INDEX.md" not in captured.out
    assert not (tmp_path / ".codex" / "session-memory" / "threads" / "target-session" / "INDEX.md").exists()
    assert not (tmp_path / ".codex" / "session-memory" / "threads" / "source-thread").exists()


def test_prepare_does_not_import_parent_locator_or_graph_store():
    checkpoint = load_checkpoint()

    assert not hasattr(checkpoint, "pl")
    assert "parent_locator.py" not in checkpoint_path_text()
    assert "graph_store.py" not in checkpoint_path_text()


def test_checkpoint_artifact_and_index_sources_do_not_depend_on_internal_graph_state():
    source_files = [
        CHECKPOINT,
        PLUGIN / "scripts" / "artifact_store.py",
        PLUGIN / "scripts" / "index_io.py",
    ]
    forbidden = [
        "parent_locator",
        "graph_store",
        "thread_spawn_edges",
        "threads.source",
        "session_meta",
        "sqlite3",
    ]

    for source_file in source_files:
        used_tokens = python_imports_names_attrs_and_runtime_strings(source_file)
        for token in forbidden:
            assert token not in used_tokens, f"{source_file.name} must not use {token}"


def python_imports_names_attrs_and_runtime_strings(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    docstring_nodes = {
        node.body[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    tokens = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            tokens.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            tokens.add(node.module)
        elif isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and not any(node is doc.value for doc in docstring_nodes)
        ):
            tokens.add(node.value)
    return tokens


def checkpoint_path_text():
    return CHECKPOINT.read_text(encoding="utf-8")


def test_prepare_does_not_call_index_update_helper(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-source-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    def fail_write_helper(*_args, **_kwargs):
        raise AssertionError("prepare must not write context or INDEX.md")

    monkeypatch.setattr(checkpoint.io, "append_context_entry_with_frontmatter", fail_write_helper)
    monkeypatch.setattr(checkpoint.io, "write_index", fail_write_helper)
    monkeypatch.setattr(checkpoint.io, "append_context_entry", fail_write_helper)
    monkeypatch.setattr(checkpoint.io, "update_frontmatter", fail_write_helper)

    assert checkpoint.main(["prepare"]) == 0

    captured = capsys.readouterr()
    context_line = next(line for line in captured.out.splitlines() if line.startswith("context_path: "))
    context_path = Path(context_line.removeprefix("context_path: "))
    assert not context_path.exists()
    assert "The active Codex must write" in captured.out


def test_prepare_outputs_deterministic_index_metadata(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-source-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return cls()

        def strftime(self, fmt):
            if fmt == "%Y%m%d-%H%M%S":
                return "20260517-101112"
            if fmt == "%Y-%m-%dT%H:%M:%SZ":
                return "2026-05-17T10:11:12Z"
            raise AssertionError(fmt)

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
    monkeypatch.setattr(checkpoint, "datetime", FakeDatetime)
    monkeypatch.setattr(checkpoint.secrets, "token_hex", lambda n: "abc123")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    expected_index = (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "target-session"
        / "INDEX.md"
    )
    assert f"index_path: {expected_index}" in output
    assert "index_entry: - [CONTEXT-20260517-101112-checkpoint-abc123.md] - <summary>" in output
    assert "last_processed_offset: 10" in output
    assert "last_updated: 2026-05-17T10:11:12Z" in output
    assert "session_id: target-session" in output
    assert "source_thread_id: source-thread" in output
    assert not expected_index.exists()


def test_prepare_unknown_argument_prints_specific_error(capsys):
    checkpoint = load_checkpoint()

    assert checkpoint.main(["prepare", "--bogus"]) == 2

    assert "unknown prepare argument" in capsys.readouterr().err


def test_verify_requires_sections_and_index_entry(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## Contexts\n\n- [{context.name}] - test\n", encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 0
    assert "verify: ok" in capsys.readouterr().out


def test_verify_accepts_flat_store_context(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "test-thread"
        / "contexts"
        / "CONTEXT-20260503-1200-test.md"
    )
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## contexts\n\n- [{context.name}] - test\n", encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

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
        f"## Contexts\n\n- [{context.name}] - child checkpoint\n",
        encoding="utf-8",
    )

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "child-thread")

    assert checkpoint.main(["verify", str(context)]) == 0
    assert "verify: ok" in capsys.readouterr().out


def test_verify_missing_session_id_exits_2(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    context = (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "test-thread"
        / "contexts"
        / "CONTEXT-20260503-1200-test.md"
    )
    write_valid_context(context)
    (context.parent.parent / "INDEX.md").write_text(
        f"## Contexts\n\n- [{context.name}] - test\n",
        encoding="utf-8",
    )
    patch_project(monkeypatch, checkpoint, tmp_path)

    assert checkpoint.main(["verify", str(context)]) == 2
    assert "CODEX_SESSION_ID" in capsys.readouterr().err


def test_verify_fails_when_required_section_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text("# test\n", encoding="utf-8")
    (context.parent.parent / "INDEX.md").write_text("", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "missing section" in capsys.readouterr().err


def test_verify_rejects_partial_graph_first_flat_context(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "test-thread"
        / "contexts"
        / "CONTEXT-20260503-1200-test.md"
    )
    context.parent.mkdir(parents=True)
    context.write_text(
        "# test\n\n"
        "## current_goal\nDone\n\n"
        "## executive_summary\nSummary\n\n"
        "## files\nFiles\n\n"
        "## next_actions\n- [ ] Next\n\n"
        "## graph_context\nthread_id: test-thread\n",
        encoding="utf-8",
    )
    (context.parent.parent / "INDEX.md").write_text(
        f"## contexts\n\n- [{context.name}] - test\n",
        encoding="utf-8",
    )
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1

    captured = capsys.readouterr()
    assert "missing section" in captured.err
    assert "## detailed_state" in captured.err


def test_prepare_missing_session_id_exits_2_and_writes_nothing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")

    assert checkpoint.main(["prepare"]) == 2
    assert "CODEX_SESSION_ID" in capsys.readouterr().err
    assert not (tmp_path / ".codex" / "session-memory").exists()


def test_prepare_fails_when_thread_id_missing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")

    assert checkpoint.main(["prepare"]) == 2
    assert "CODEX_THREAD_ID" in capsys.readouterr().err


def test_prepare_fails_when_jsonl_missing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "source-thread")
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
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not exist" in capsys.readouterr().err


def test_verify_fails_when_index_reference_missing(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    (context.parent.parent / "INDEX.md").write_text("## Contexts\n", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not include context entry" in capsys.readouterr().err


def test_verify_rejects_context_path_outside_project_session_tree(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path.parent / "outside-contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "outside project session contexts" in capsys.readouterr().err


def test_verify_rejects_section_substring_false_positive(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    context.parent.mkdir(parents=True)
    context.write_text(
        "# test\n\n"
        "Paragraph mentions ## current_goal but is not a heading line.\n\n"
        "## executive_summary\nSummary\n\n"
        "## detailed_state\nState\n\n"
        "## decisions\nDecision\n\n"
        "## files\nFiles\n\n"
        "## verification\nTests\n\n"
        "## risks\nNone\n\n"
        "## next_actions\n- [ ] Next\n\n"
        "## graph_context\nGraph\n",
        encoding="utf-8",
    )
    (context.parent.parent / "INDEX.md").write_text(f"- [{context.name}] - test\n", encoding="utf-8")
    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

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
    monkeypatch.setenv("CODEX_SESSION_ID", "test-thread")

    assert checkpoint.main(["verify", str(context)]) == 1
    assert "INDEX.md does not include context entry" in capsys.readouterr().err


def test_prepare_outputs_context_and_index_targets_without_writing(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    session_dir = tmp_path / ".codex" / "session-memory" / "threads" / "target-session"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 12))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    context_line = next(line for line in output.splitlines() if line.startswith("context_path: "))
    context_path = Path(context_line.removeprefix("context_path: "))
    assert not context_path.exists()
    assert not (session_dir / "INDEX.md").exists()
    assert f"index_entry: - [{context_path.name}] - <summary>" in output


def test_root_errors_return_clear_stderr(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    monkeypatch.setattr(checkpoint.os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(checkpoint.dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setenv("CODEX_SESSION_ID", "target-session")
    monkeypatch.setenv("CODEX_THREAD_ID", "test-thread")
    monkeypatch.setattr(checkpoint.pr, "find_project_root", lambda cwd: str(tmp_path))

    def fail_root(root, cwd):
        raise RuntimeError("not canonical")

    monkeypatch.setattr(checkpoint.pr, "assert_root_is_canonical", fail_root)

    assert checkpoint.main(["prepare"]) == 2
    assert "not canonical" in capsys.readouterr().err
