import importlib.util
import json
import sqlite3
from pathlib import Path
from typing import Optional


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory"
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


SECTION_GUIDANCE = {
    "## current_goal": "approved current goal and scope",
    "## executive_summary": "3-7 lines",
    "## detailed_state": "workflow, judgments, and confirmed facts",
    "## decisions": "decisions, rationale, alternatives, and fallback",
    "## files": "per-file change reason and next check point",
    "## verification": "commands, results, failure causes, and unverified items",
    "## risks": "remaining risks and uncertain assumptions",
    "## next_actions": "ordered steps the next person can run immediately",
    "## graph_context": "thread id, graph role, parent id, and graph lookup status",
}


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
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(
        checkpoint.sl,
        "artifact_session_dir",
        lambda root, thread_id: tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / thread_id,
    )
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([{"role": "assistant", "text": "Run `git status --short`"}], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "thread_id: test-thread" in output
    assert "context_path:" in output
    assert "INDEX.md" in output
    assert "git status --short" in output
    assert "## current_goal" in output
    assert "index_entry: -" in output
    assert "last_processed_offset: 10" in output


def test_prepare_outputs_flat_artifact_target(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(
        checkpoint.sl,
        "artifact_session_dir",
        lambda root, thread_id: tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / thread_id,
    )
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert ".codex/session-memory/threads/test-thread/INDEX.md" in output
    assert "_children" not in output
    for heading, guidance in SECTION_GUIDANCE.items():
        assert heading in output
        assert guidance in output


def test_prepare_frontmatter_update_excludes_relationship_source_fields(
    monkeypatch, tmp_path, capsys
):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(
        checkpoint.sl,
        "artifact_session_dir",
        lambda root, thread_id: tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / thread_id,
    )
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child", "--parent", "parent-thread"]) == 0

    output = capsys.readouterr().out
    frontmatter_update = output.split("frontmatter_update:", 1)[1].split("\n\n", 1)[0]
    assert "last_processed_offset: 10" in frontmatter_update
    assert "last_updated: <ISO-8601 timestamp>" in frontmatter_update
    assert "session_id: <thread_id>" in frontmatter_update
    assert "role:" not in frontmatter_update
    assert "parent_session_id:" not in frontmatter_update
    assert "relationship_diagnostics:" in output
    assert "relationship_source: argument" in output


def test_prepare_marks_graph_unavailable_when_parent_resolution_has_no_source(
    monkeypatch,
    tmp_path,
    capsys,
):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(
        checkpoint.sl,
        "artifact_session_dir",
        lambda root, thread_id: tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / thread_id,
    )
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))
    monkeypatch.setattr(
        checkpoint.pl,
        "resolve_parent_thread_id",
        lambda **kwargs: checkpoint.pl.ParentResolution(
            role="main",
            source="none",
            confidence="none",
            reason="graph unavailable",
            warnings=("state db unavailable",),
        ),
    )

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "## graph_context" in output
    graph_context = output.split("## graph_context", 1)[1]
    assert "thread_id: test-thread" in graph_context
    assert "graph_role: main" in graph_context
    assert "parent_session_id: " in graph_context
    assert "graph_status: unavailable" in graph_context
    assert "graph_reason: graph unavailable" in output
    assert "graph_warnings: state db unavailable" in output


def test_prepare_uses_hh00_context_path_and_reuses_existing_file(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-test-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    session_dir = tmp_path / ".codex" / "session-memory" / "threads" / "test-thread"
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
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: session_dir)
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
    child_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output
    assert "relationship_source: rollout_session_meta" in output


def test_prepare_parent_without_role_is_child_intent(monkeypatch, tmp_path, capsys):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    child_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: child_dir)
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
    child_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SESSION_PARENT_ID", "env-parent-thread")
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: env-parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output
    assert "relationship_source: environment" in output


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


def test_prepare_uses_state_db_when_rollout_child_parent_missing(
    monkeypatch,
    tmp_path,
    capsys,
):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    write_child_session_meta(jsonl, parent_thread_id=None)
    sqlite_home = tmp_path / "sqlite-home"
    db = sqlite_home / "state_5.sqlite"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE thread_spawn_edges ("
        "parent_thread_id TEXT NOT NULL, "
        "child_thread_id TEXT NOT NULL PRIMARY KEY, "
        "status TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-from-db", "child-thread", "open"),
    )
    conn.commit()
    conn.close()
    child_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setenv("CODEX_SQLITE_HOME", str(sqlite_home))
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-from-db" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output


def test_prepare_passes_project_codex_home_to_parent_locator(
    monkeypatch,
    tmp_path,
):
    checkpoint = load_checkpoint()
    jsonl = tmp_path / "rollout-child-thread.jsonl"
    jsonl.write_text('{"type":"turn","payload":"ok"}\n', encoding="utf-8")
    calls = []

    def resolve_parent_thread_id(*, thread_id, rollout_path, codex_home=None):
        calls.append((thread_id, rollout_path, codex_home))
        return checkpoint.pl.ParentResolution(role="main")

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert checkpoint.main(["prepare", "--role", "child"]) == 2

    assert calls == [("child-thread", jsonl, tmp_path / ".codex")]


def test_prepare_checks_parent_resolution_before_jsonl_missing_failure(
    monkeypatch, tmp_path, capsys
):
    checkpoint = load_checkpoint()
    calls = []

    def resolve_parent_thread_id(*, thread_id, rollout_path, codex_home=None):
        calls.append((thread_id, rollout_path, codex_home))
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
    assert calls == [("child-thread", None, tmp_path / ".codex")]
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
    child_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "child-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: child_dir)
    monkeypatch.setattr(checkpoint.io, "read_frontmatter", lambda path: {"last_processed_offset": 0})
    monkeypatch.setattr(checkpoint.jp, "extract_delta", lambda path, offset: ([], 10))

    assert checkpoint.main(["prepare", "--role", "child", "--parent", "parent-thread"]) == 0

    output = capsys.readouterr().out
    assert "role: child" in output
    assert "parent_session_id: parent-thread" in output
    assert f"index_path: {child_dir / 'INDEX.md'}" in output
    assert "parent_index_path: " in output
    assert "_children" not in output
    assert "parent_child_entry:" in output


def test_verify_requires_sections_and_index_entry(tmp_path, monkeypatch, capsys):
    checkpoint = load_checkpoint()
    context = tmp_path / ".codex" / "sessions" / "test-thread" / "contexts" / "CONTEXT-20260503-1200-test.md"
    write_valid_context(context)
    index = context.parent.parent / "INDEX.md"
    index.write_text(f"## Contexts\n\n- [{context.name}] - test\n", encoding="utf-8")

    patch_project(monkeypatch, checkpoint, tmp_path)

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

    assert checkpoint.main(["verify", str(context)]) == 1

    captured = capsys.readouterr()
    assert "missing section" in captured.err
    assert "## detailed_state" in captured.err


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
    (context.parent.parent / "INDEX.md").write_text("## Contexts\n", encoding="utf-8")
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
    session_dir = tmp_path / ".codex" / "session-memory" / "threads" / "test-thread"

    patch_project(monkeypatch, checkpoint, tmp_path)
    monkeypatch.setattr(checkpoint.sl, "current_thread_id", lambda: "test-thread")
    monkeypatch.setattr(checkpoint.sl, "find_jsonl_by_thread", lambda thread_id: jsonl)
    monkeypatch.setattr(checkpoint.sl, "artifact_session_dir", lambda root, thread_id: session_dir)
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
