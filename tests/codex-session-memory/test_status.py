import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory"
STATUS = PLUGIN / "skills" / "status" / "status.py"


@pytest.fixture(autouse=True)
def isolate_default_codex_home(monkeypatch, tmp_path):
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home-without-codex"))


def load_status():
    module_name = "test_codex_session_memory_status"
    spec = importlib.util.spec_from_file_location(module_name, STATUS)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def make_graph_state_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE thread_spawn_edges ("
        "parent_thread_id TEXT NOT NULL, "
        "child_thread_id TEXT NOT NULL PRIMARY KEY, "
        "status TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def insert_graph_edge(path: Path, parent: str, child: str, status: str = "open"):
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO thread_spawn_edges VALUES (?, ?, ?)", (parent, child, status))
    conn.commit()
    conn.close()


def configure_status_common(monkeypatch, status, tmp_path, thread_id, jsonl_path=None):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: thread_id)
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda _thread_id: jsonl_path)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )


def write_flat_index(tmp_path, thread_id, *, last_updated="flat-current", last_offset=0):
    flat_dir = tmp_path / ".codex" / "session-memory" / "threads" / thread_id
    flat_dir.mkdir(parents=True)
    (flat_dir / "INDEX.md").write_text(
        "---\n"
        f"last_updated: {last_updated}\n"
        f"last_processed_offset: {last_offset}\n"
        f"session_id: {thread_id}\n"
        "---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    return flat_dir


def test_status_reports_main_role_and_direct_children_from_graph(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    write_flat_index(tmp_path, "parent-thread", last_offset=42)
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_graph_state_db(db)
    insert_graph_edge(db, "parent-thread", "child-thread")

    configure_status_common(monkeypatch, status, tmp_path, "parent-thread")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Last saved: flat-current" in output
    assert "Role: main" in output
    assert "Direct children: 1" in output
    assert "Child sessions:" not in output


def test_status_reports_child_role_parent_and_zero_children_from_graph(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    write_flat_index(tmp_path, "child-thread")
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_graph_state_db(db)
    insert_graph_edge(db, "parent-thread", "child-thread")

    configure_status_common(monkeypatch, status, tmp_path, "child-thread")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent thread: parent-thread" in output
    assert "Direct children: 0" in output
    assert "Child sessions:" not in output


def test_status_reports_graph_unavailable_without_failing(monkeypatch, tmp_path, capsys):
    status = load_status()
    write_flat_index(tmp_path, "thread-without-graph")
    configure_status_common(monkeypatch, status, tmp_path, "thread-without-graph")
    monkeypatch.setattr(
        status.Path,
        "home",
        classmethod(lambda cls: tmp_path / "home-without-state-db"),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Graph: unavailable" in output
    assert "Last saved: flat-current" in output


def test_status_does_not_use_default_home_graph_when_project_graph_is_missing(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    write_flat_index(tmp_path, "project-thread")
    fake_home = tmp_path / "fake-home"
    home_db = fake_home / ".codex" / "state_5.sqlite"
    make_graph_state_db(home_db)
    insert_graph_edge(home_db, "project-thread", "home-child")

    configure_status_common(monkeypatch, status, tmp_path, "project-thread")
    monkeypatch.setattr(status.Path, "home", classmethod(lambda cls: fake_home))

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Graph: unavailable" in output
    assert "Direct children: 1" not in output


def test_status_passes_project_codex_home_to_graph_store(monkeypatch, tmp_path):
    status = load_status()
    write_flat_index(tmp_path, "abc123")
    configure_status_common(monkeypatch, status, tmp_path, "abc123")
    calls = []

    class FakeGraphStore:
        def __init__(self, *, codex_home, include_default_home=True):
            calls.append((codex_home, include_default_home))

        def role_of(self, thread_id):
            return SimpleNamespace(role="main", available=False)

    monkeypatch.setattr(status, "GraphStore", FakeGraphStore)

    assert status.main() == 0

    assert calls == [(tmp_path / ".codex", False)]


def test_status_prints_checkpointed_session_fields(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    (contexts_dir / "CONTEXT-20260502-1200-test.md").write_text("# test\n")
    index_path = session_dir / "INDEX.md"
    index_path.write_text("---\nlast_updated: 2026-05-02T00:00:00Z\nlast_processed_offset: 42\n---\n")
    child = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nrole: child\nparent_session_id: abc123\n---\n\n# Child\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-test-abc123.jsonl"
    jsonl_path.write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    def fake_read_frontmatter(path):
        if "child123" in str(path):
            return {"role": "child", "parent_session_id": "abc123"}
        return {"last_updated": "2026-05-02T00:00:00Z", "last_processed_offset": 42}

    monkeypatch.setattr(status.csm_index_io, "read_frontmatter", fake_read_frontmatter)
    monkeypatch.setattr(status.csm_jsonl_parser, "extract_delta", lambda path, offset: ([{"role": "user"}], 84))
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Project root: {tmp_path}" in output
    assert "Thread id: abc123" in output
    assert f"JSONL path: {jsonl_path}" in output
    assert "Context files: 1" in output
    assert "Last saved: 2026-05-02T00:00:00Z" in output
    assert "Pending offset: 42" in output
    assert "AGENTS.md rules: installed" in output
    assert "Hooks:" not in output
    assert "Child sessions: 1" in output
    assert "pending_turns: 1" in output


def test_status_prefers_flat_artifact_current_session(monkeypatch, tmp_path, capsys):
    status = load_status()
    flat_dir = tmp_path / ".codex" / "session-memory" / "threads" / "abc123"
    flat_contexts = flat_dir / "contexts"
    flat_contexts.mkdir(parents=True)
    (flat_contexts / "CONTEXT-20260504-1200-test.md").write_text("# flat\n", encoding="utf-8")
    (flat_dir / "INDEX.md").write_text(
        "---\nlast_updated: flat-current\nlast_processed_offset: 42\nsession_id: abc123\n---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    legacy_dir = tmp_path / ".codex" / "sessions" / "abc123"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "INDEX.md").write_text(
        "---\nlast_updated: legacy-stale\nlast_processed_offset: 1\n---\n\n"
        "# Legacy\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-test-abc123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )
    monkeypatch.setattr(status.csm_jsonl_parser, "extract_delta", lambda path, offset: ([], 42))

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Artifact path: {flat_dir}" in output
    assert "Context files: 1" in output
    assert "Last saved: flat-current" in output
    assert "Pending offset: 42" in output
    assert str(legacy_dir) not in output
    assert "Last saved: legacy-stale" not in output


def test_status_uses_main_artifact_when_project_graph_role_is_main_with_stale_child(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "main-thread"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-current\n"
        "last_processed_offset: 42\n"
        "---\n\n"
        "# Main\n",
        encoding="utf-8",
    )
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "main-thread"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: stale-parent\n"
        "last_updated: child-stale\n"
        "last_processed_offset: 1\n"
        "---\n\n"
        "# Stale child\n",
        encoding="utf-8",
    )
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_graph_state_db(db)
    insert_graph_edge(db, "main-thread", "real-child")

    configure_status_common(monkeypatch, status, tmp_path, "main-thread")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: main" in output
    assert f"Artifact path: {main_dir}" in output
    assert "Last saved: main-current" in output
    assert str(child_dir) not in output
    assert "Last saved: child-stale" not in output


def test_status_uses_graph_child_info_for_flat_artifact_without_relationship_frontmatter(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    flat_dir = tmp_path / ".codex" / "session-memory" / "threads" / "child123"
    flat_contexts = flat_dir / "contexts"
    flat_contexts.mkdir(parents=True)
    (flat_contexts / "CONTEXT-20260504-1200-test.md").write_text("# flat\n", encoding="utf-8")
    (flat_dir / "INDEX.md").write_text(
        "---\nlast_updated: flat-child\nlast_processed_offset: 42\nsession_id: child123\n---\n\n"
        "# Flat Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(
            resolve_parent_thread_id=lambda thread_id, rollout_path=None, **kwargs: SimpleNamespace(
                role="child",
                parent_thread_id="parent123",
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )
    monkeypatch.setattr(status.csm_jsonl_parser, "extract_delta", lambda path, offset: ([], 42))

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert f"Parent INDEX.md: {parent_index}" in output
    assert "Child sessions:" not in output
    assert "Last saved: flat-child" in output


@pytest.mark.parametrize(("children_present", "expected_count"), ((False, 0), (True, 1)))
def test_status_child_count_is_stable_when_children_dir_absent_or_present(
    monkeypatch, tmp_path, capsys, children_present, expected_count
):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    session_dir.mkdir(parents=True)
    (session_dir / "INDEX.md").write_text(
        "---\nlast_updated: 2026-05-02T00:00:00Z\nlast_processed_offset: 0\n---\n",
        encoding="utf-8",
    )
    if children_present:
        child = tmp_path / ".codex" / "sessions" / "_children" / "child123"
        child.mkdir(parents=True)
        (child / "INDEX.md").write_text(
            "---\nrole: child\nparent_session_id: abc123\n---\n\n# Child\n",
            encoding="utf-8",
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Child sessions: {expected_count}" in output


def test_status_prints_child_parent_information(monkeypatch, tmp_path, capsys):
    status = load_status()
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert f"Parent INDEX.md: {parent_index.resolve()}" in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" not in output


def test_status_prefers_child_session_when_both_main_and_child_indexes_exist(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: child-current\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Current child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert "Last saved: child-current" in output
    assert "Last saved: main-stale" not in output


def test_status_reports_uncheckpointed_child_from_parent_evidence_before_stale_main(
    monkeypatch,
    tmp_path,
    capsys,
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(
            resolve_parent_thread_id=lambda thread_id, rollout_path=None, **kwargs: SimpleNamespace(
                role="child",
                parent_thread_id="parent123",
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert "Last saved: main-stale" not in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" in output


def test_status_reports_uncheckpointed_child_with_unknown_parent_before_stale_main(
    monkeypatch,
    tmp_path,
    capsys,
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(
            resolve_parent_thread_id=lambda thread_id, rollout_path=None, **kwargs: SimpleNamespace(
                role="child",
                parent_thread_id=None,
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: unknown" in output
    assert "Parent INDEX.md: missing" in output
    assert "Last saved: main-stale" not in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" in output


def test_status_passes_project_codex_home_to_parent_locator(monkeypatch, tmp_path):
    status = load_status()
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    calls = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    def resolve_parent_thread_id(thread_id, rollout_path=None, codex_home=None):
        calls.append((thread_id, rollout_path, codex_home))
        return SimpleNamespace(role="main", parent_thread_id=None)

    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(resolve_parent_thread_id=resolve_parent_thread_id),
        raising=False,
    )

    assert status.main() == 0

    assert calls == [("child123", jsonl_path, tmp_path / ".codex")]


def test_status_old_data_session_dir_signature_still_finds_child_session(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    def old_data_session_dir(root, thread_id):
        return main_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", old_data_session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert f"Parent INDEX.md: {parent_index.resolve()}" in output
    assert "status: not yet checkpointed" not in output


def test_status_data_session_dir_internal_type_error_is_not_swallowed(monkeypatch, tmp_path):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    def broken_data_session_dir(root, thread_id, role=None):
        if role is not None:
            raise TypeError("internal bug")
        return session_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", broken_data_session_dir)

    with pytest.raises(TypeError, match="internal bug"):
        status.main()


def test_status_parent_index_path_falls_back_without_parent_session_dir(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(status.csm_session_locator, "parent_session_dir")
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Parent INDEX.md: {parent_index}" in output


@pytest.mark.parametrize(
    ("rules_status", "missing_markers"),
    (
        ("partial", ("CODEX_THREAD_ID", ".codex/")),
        ("missing", ("$session-memory:checkpoint", "CODEX_THREAD_ID", ".codex/")),
    ),
)
def test_status_prints_missing_values_before_checkpoint(
    monkeypatch, tmp_path, capsys, rules_status, missing_markers
):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status=rules_status, missing=missing_markers),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "JSONL path: missing" in output
    assert "Context files: 0" in output
    assert "Last saved: never" in output
    assert "Pending offset: 0" in output
    assert f"AGENTS.md rules: {rules_status}" in output
    assert f"AGENTS.md missing markers: {', '.join(missing_markers)}" in output
    assert "Hooks:" not in output
    assert "status: not yet checkpointed" in output


def test_status_uses_real_partial_agents_rules_report(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    (tmp_path / "AGENTS.md").write_text(
        "# Project Rules\n\n"
        "$session-memory:checkpoint\n"
        "$session-memory:status\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "AGENTS.md rules: partial" in output
    assert "$session-memory:resume" in output
    assert "CODEX_THREAD_ID" in output
    assert "$session-memory:checkpoint" not in output
    assert "$session-memory:status" not in output
    assert "Hooks:" not in output


def test_status_uses_real_not_found_agents_rules_report(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "AGENTS.md rules: not found" in output
    assert "AGENTS.md missing markers:" in output
    assert "$session-memory:checkpoint" in output
    assert "Hooks:" not in output


def test_status_without_thread_id_returns_zero(monkeypatch, tmp_path, capsys):
    status = load_status()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "CODEX_THREAD_ID: not set" in output
    assert "Hooks:" not in output
