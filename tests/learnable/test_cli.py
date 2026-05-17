from __future__ import annotations

import json
import sys
from collections.abc import Callable
from io import StringIO
from pathlib import Path

import pytest

from learnable.cli import main

StorageMutator = Callable[[Path], None]


def _materials_root(project_root: Path) -> Path:
    return project_root / ".codex" / "materials"


def _session_dirs(project_root: Path) -> list[Path]:
    sessions = _materials_root(project_root) / "sessions"
    if not sessions.exists():
        return []
    return sorted(path for path in sessions.iterdir() if path.is_dir())


def _session_record(project_root: Path) -> dict[str, object]:
    session_path = _session_dirs(project_root)[0] / "session.json"
    return json.loads(session_path.read_text(encoding="utf-8"))


def _root_node_dir(project_root: Path) -> Path:
    session = _session_record(project_root)
    return (
        _materials_root(project_root)
        / "sessions"
        / str(session["learnable_session_id"])
        / "nodes"
        / str(session["root_node_id"])
    )


def _materials_snapshot(project_root: Path) -> dict[str, str]:
    root = _materials_root(project_root)
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_no_session_memory(project_root: Path) -> None:
    assert not (project_root / ".codex" / "session-memory").exists()


def _run(project_root: Path, *args: str) -> int:
    return main(["--project-root", str(project_root), *args])


def test_init_creates_cli_storage_without_session_memory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _run(tmp_path, "init")

    output = capsys.readouterr().out
    assert result == 0
    assert (_materials_root(tmp_path) / "index.json").is_file()
    assert (_materials_root(tmp_path) / ".server" / "config.json").is_file()
    assert "initialized" in output
    assert str(tmp_path) not in output
    _assert_no_session_memory(tmp_path)


def test_ask_stores_markdown_file_as_root_material(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown = tmp_path / "answer.md"
    markdown.write_text("# Root\n\nAnswer body.\n", encoding="utf-8")

    result = _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain TOKEN=learnable-token-12345",
        "--markdown-file",
        str(markdown),
    )

    output = capsys.readouterr().out
    session = _session_record(tmp_path)
    node_dir = _root_node_dir(tmp_path)
    material = json.loads((node_dir / "material.json").read_text(encoding="utf-8"))
    assert result == 0
    assert "learnable_session_id=" in output
    assert "root_node_id=" in output
    assert "learnable-token-12345" not in output
    assert session["title"] == "Root"
    assert material["created_from_prompt"] == "Explain TOKEN=[REDACTED:assignment]"
    assert (node_dir / "node.md").read_text(encoding="utf-8") == "# Root\n\nAnswer body.\n"
    _assert_no_session_memory(tmp_path)


def test_ask_reads_markdown_from_stdin_when_file_is_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO("stdin body\n"))

    result = _run(tmp_path, "ask", "--title", "Root", "--prompt", "Explain")

    assert result == 0
    assert (_root_node_dir(tmp_path) / "node.md").read_text(encoding="utf-8") == (
        "stdin body\n"
    )
    _assert_no_session_memory(tmp_path)


@pytest.mark.parametrize(
    "args",
    [
        ("ask", "--title", "Root", "--prompt", "Explain", "--markdown-file", "missing.md"),
        ("ask", "--title", "Root", "--prompt", "Explain", "--markdown-file", "."),
    ],
)
def test_ask_markdown_file_read_failures_do_not_update_storage(
    tmp_path: Path,
    args: tuple[str, ...],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(tmp_path, "init")
    before_index = (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8")
    capsys.readouterr()

    result = _run(tmp_path, *args)

    captured = capsys.readouterr()
    assert result != 0
    assert "error:" in captured.err
    assert str(tmp_path) not in captured.err
    assert (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8") == before_index
    assert _session_dirs(tmp_path) == []
    _assert_no_session_memory(tmp_path)


def test_ask_empty_markdown_file_does_not_update_storage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty = tmp_path / "empty.md"
    empty.write_text("", encoding="utf-8")
    _run(tmp_path, "init")
    before_index = (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8")
    capsys.readouterr()

    result = _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(empty),
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "empty markdown" in captured.err
    assert (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8") == before_index
    assert _session_dirs(tmp_path) == []
    _assert_no_session_memory(tmp_path)


def test_ask_empty_stdin_does_not_update_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(""))
    _run(tmp_path, "init")
    before_index = (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8")
    capsys.readouterr()

    result = _run(tmp_path, "ask", "--title", "Root", "--prompt", "Explain")

    captured = capsys.readouterr()
    assert result != 0
    assert "empty markdown" in captured.err
    assert (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8") == before_index
    assert _session_dirs(tmp_path) == []
    _assert_no_session_memory(tmp_path)


def test_ask_missing_markdown_source_does_not_update_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class MissingStdin:
        def isatty(self) -> bool:
            return True

        def read(self) -> str:
            raise AssertionError("stdin should not be read when no source exists")

    monkeypatch.setattr(sys, "stdin", MissingStdin())
    _run(tmp_path, "init")
    before_index = (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8")
    capsys.readouterr()

    result = _run(tmp_path, "ask", "--title", "Root", "--prompt", "Explain")

    captured = capsys.readouterr()
    assert result != 0
    assert "missing markdown source" in captured.err
    assert (_materials_root(tmp_path) / "index.json").read_text(encoding="utf-8") == before_index
    assert _session_dirs(tmp_path) == []
    _assert_no_session_memory(tmp_path)


def test_explain_adds_child_material_from_markdown_file(tmp_path: Path) -> None:
    root_markdown = tmp_path / "root.md"
    child_markdown = tmp_path / "child.md"
    root_markdown.write_text("# Root\n", encoding="utf-8")
    child_markdown.write_text("## Child\n", encoding="utf-8")
    assert _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(root_markdown),
    ) == 0
    session = _session_record(tmp_path)

    result = _run(
        tmp_path,
        "explain",
        "--session",
        str(session["learnable_session_id"]),
        "--parent",
        str(session["root_node_id"]),
        "--title",
        "Child",
        "--prompt",
        "More",
        "--markdown-file",
        str(child_markdown),
    )

    graph = json.loads((_session_dirs(tmp_path)[0] / "graph.json").read_text(encoding="utf-8"))
    child_ids = set(graph["nodes"]) - {session["root_node_id"]}
    assert result == 0
    assert len(child_ids) == 1
    child_dir = _session_dirs(tmp_path)[0] / "nodes" / child_ids.pop()
    assert (child_dir / "node.md").read_text(encoding="utf-8") == "## Child\n"
    _assert_no_session_memory(tmp_path)


def test_explain_reads_markdown_from_stdin_when_file_is_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_markdown = tmp_path / "root.md"
    root_markdown.write_text("# Root\n", encoding="utf-8")
    assert _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(root_markdown),
    ) == 0
    session = _session_record(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO("stdin child\n"))

    result = _run(
        tmp_path,
        "explain",
        "--session",
        str(session["learnable_session_id"]),
        "--parent",
        str(session["root_node_id"]),
        "--title",
        "Child",
        "--prompt",
        "More",
    )

    graph = json.loads((_session_dirs(tmp_path)[0] / "graph.json").read_text(encoding="utf-8"))
    child_ids = set(graph["nodes"]) - {session["root_node_id"]}
    child_dir = _session_dirs(tmp_path)[0] / "nodes" / child_ids.pop()
    assert result == 0
    assert (child_dir / "node.md").read_text(encoding="utf-8") == "stdin child\n"
    _assert_no_session_memory(tmp_path)


@pytest.mark.parametrize(
    "markdown_file",
    [
        "empty.md",
        "missing.md",
    ],
)
def test_explain_markdown_input_failures_do_not_mutate_materials(
    tmp_path: Path,
    markdown_file: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root_markdown = tmp_path / "root.md"
    root_markdown.write_text("# Root\n", encoding="utf-8")
    empty_markdown = tmp_path / "empty.md"
    empty_markdown.write_text("", encoding="utf-8")
    assert _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(root_markdown),
    ) == 0
    session = _session_record(tmp_path)
    before = _materials_snapshot(tmp_path)
    capsys.readouterr()

    result = _run(
        tmp_path,
        "explain",
        "--session",
        str(session["learnable_session_id"]),
        "--parent",
        str(session["root_node_id"]),
        "--title",
        "Child",
        "--prompt",
        "More",
        "--markdown-file",
        str(tmp_path / markdown_file),
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "error:" in captured.err
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


def test_explain_empty_stdin_does_not_mutate_materials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root_markdown = tmp_path / "root.md"
    root_markdown.write_text("# Root\n", encoding="utf-8")
    assert _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(root_markdown),
    ) == 0
    session = _session_record(tmp_path)
    before = _materials_snapshot(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO(""))
    capsys.readouterr()

    result = _run(
        tmp_path,
        "explain",
        "--session",
        str(session["learnable_session_id"]),
        "--parent",
        str(session["root_node_id"]),
        "--title",
        "Child",
        "--prompt",
        "More",
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "empty markdown" in captured.err
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


def test_explain_missing_stdin_source_does_not_mutate_materials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class MissingStdin:
        def isatty(self) -> bool:
            return True

        def read(self) -> str:
            raise AssertionError("stdin should not be read when no source exists")

    root_markdown = tmp_path / "root.md"
    root_markdown.write_text("# Root\n", encoding="utf-8")
    assert _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(root_markdown),
    ) == 0
    session = _session_record(tmp_path)
    before = _materials_snapshot(tmp_path)
    monkeypatch.setattr(sys, "stdin", MissingStdin())
    capsys.readouterr()

    result = _run(
        tmp_path,
        "explain",
        "--session",
        str(session["learnable_session_id"]),
        "--parent",
        str(session["root_node_id"]),
        "--title",
        "Child",
        "--prompt",
        "More",
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "missing markdown source" in captured.err
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


def test_status_prints_redacted_storage_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown = tmp_path / "answer.md"
    markdown.write_text("# Root\n", encoding="utf-8")
    _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(markdown),
    )
    token_path = _materials_root(tmp_path) / ".server" / "token"
    token_path.write_text("learnable-token-12345\n", encoding="utf-8")
    before = _materials_snapshot(tmp_path)
    capsys.readouterr()

    result = _run(tmp_path, "status")

    output = capsys.readouterr().out
    assert result == 0
    assert "materials_root=" in output
    assert "server_config=" in output
    assert "sessions_count=1" in output
    assert "schema_version=1.0" in output
    assert str(tmp_path) not in output
    assert "learnable-token-12345" not in output
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


def test_status_reports_missing_storage_without_creating_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _run(tmp_path, "status")

    output = capsys.readouterr().out
    assert result == 0
    assert "materials_root=.codex/materials" in output
    assert "server_config=missing" in output
    assert "sessions_count=0" in output
    assert "schema_version=missing" in output
    assert str(tmp_path) not in output
    assert not _materials_root(tmp_path).exists()
    _assert_no_session_memory(tmp_path)


def test_validate_accepts_valid_storage_without_creating_session_memory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown = tmp_path / "answer.md"
    markdown.write_text("# Root\n", encoding="utf-8")
    _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(markdown),
    )
    before = _materials_snapshot(tmp_path)
    capsys.readouterr()

    result = _run(tmp_path, "validate")

    assert result == 0
    assert "valid" in capsys.readouterr().out
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


@pytest.mark.parametrize(
    ("case_name", "mutate"),
    [
        (
            "invalid_schema",
            lambda root: _write_json(
                _root_node_dir(root) / "material.json",
                {"schema_version": "1.0"},
            ),
        ),
        (
            "invalid_graph",
            lambda root: _write_graph_field(root, "root_node_id", "node-missing"),
        ),
        (
            "session_id_mismatch",
            lambda root: _write_session_field(
                root,
                "learnable_session_id",
                "learnable-session-mismatch",
            ),
        ),
        (
            "graph_session_id_mismatch",
            lambda root: _write_graph_field(
                root,
                "learnable_session_id",
                "learnable-session-mismatch",
            ),
        ),
        (
            "session_graph_root_node_mismatch",
            lambda root: _write_session_field(root, "root_node_id", "node-mismatch"),
        ),
        (
            "missing_server_config",
            lambda root: (_materials_root(root) / ".server" / "config.json").unlink(),
        ),
        (
            "missing_server_token",
            lambda root: (_materials_root(root) / ".server" / "token").unlink(),
        ),
        (
            "invalid_server_config",
            lambda root: _write_json(_materials_root(root) / ".server" / "config.json", {}),
        ),
        (
            "server_config_path_mismatch",
            lambda root: _write_server_config_field(root, "tokenPath", "/outside/token"),
        ),
        ("missing_markdown_body", lambda root: (_root_node_dir(root) / "node.md").unlink()),
        (
            "orphan_node_directory",
            lambda root: (_session_dirs(root)[0] / "nodes" / "node-orphan").mkdir(),
        ),
        (
            "malformed_json",
            lambda root: (_session_dirs(root)[0] / "graph.json").write_text("{", encoding="utf-8"),
        ),
        (
            "malformed_event_jsonl",
            lambda root: (_session_dirs(root)[0] / "events.jsonl").write_text("{\n", encoding="utf-8"),
        ),
        (
            "invalid_event_schema",
            lambda root: (_session_dirs(root)[0] / "events.jsonl").write_text(
                '{"foo":"bar"}\n',
                encoding="utf-8",
            ),
        ),
        (
            "malformed_audit_jsonl",
            lambda root: (
                _materials_root(root) / ".server" / "audits.jsonl"
            ).write_text("{\n", encoding="utf-8"),
        ),
        (
            "invalid_audit_schema",
            lambda root: (
                _materials_root(root) / ".server" / "audits.jsonl"
            ).write_text('{"foo":"bar"}\n', encoding="utf-8"),
        ),
    ],
)
def test_validate_rejects_invalid_storage_without_repairing(
    tmp_path: Path,
    case_name: str,
    mutate: StorageMutator,
    capsys: pytest.CaptureFixture[str],
) -> None:
    markdown = tmp_path / "answer.md"
    markdown.write_text("# Root\n", encoding="utf-8")
    _run(
        tmp_path,
        "ask",
        "--title",
        "Root",
        "--prompt",
        "Explain",
        "--markdown-file",
        str(markdown),
    )
    before_sessions = sorted(path.name for path in _session_dirs(tmp_path))
    mutate(tmp_path)
    before = _materials_snapshot(tmp_path)
    capsys.readouterr()

    result = _run(tmp_path, "validate")

    captured = capsys.readouterr()
    assert result != 0, case_name
    assert "error:" in captured.err
    assert str(tmp_path) not in captured.err
    assert "learnable-token-12345" not in captured.err
    assert sorted(path.name for path in _session_dirs(tmp_path)) == before_sessions
    assert _materials_snapshot(tmp_path) == before
    _assert_no_session_memory(tmp_path)


def test_help_exits_successfully_without_creating_storage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["--project-root", str(tmp_path), "--help"])

    captured = capsys.readouterr()
    assert result == 0
    assert "usage: learnable" in captured.out
    assert not _materials_root(tmp_path).exists()
    _assert_no_session_memory(tmp_path)


@pytest.mark.parametrize(
    "args",
    [
        ("unknown",),
        ("ask", "--title", "Root"),
    ],
)
def test_parser_errors_exit_without_creating_storage(
    tmp_path: Path,
    args: tuple[str, ...],
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["--project-root", str(tmp_path), *args])

    captured = capsys.readouterr()
    assert result == 2
    assert "usage:" in captured.err
    assert not _materials_root(tmp_path).exists()
    _assert_no_session_memory(tmp_path)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_session_field(project_root: Path, field: str, value: object) -> None:
    session_path = _session_dirs(project_root)[0] / "session.json"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    session[field] = value
    _write_json(session_path, session)


def _write_graph_field(project_root: Path, field: str, value: object) -> None:
    graph_path = _session_dirs(project_root)[0] / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph[field] = value
    _write_json(graph_path, graph)


def _write_server_config_field(project_root: Path, field: str, value: object) -> None:
    config_path = _materials_root(project_root) / ".server" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config[field] = value
    _write_json(config_path, config)
