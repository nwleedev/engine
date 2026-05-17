from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import pytest

from learnable.materials.file_store import FileMaterialStore
from learnable.materials.store import MaterialStore


def _provenance() -> dict[str, object]:
    return {
        "runtime": "codex",
        "codex_session_id": "runtime-session-a",
        "codex_thread_id": "runtime-thread-a",
    }


def _create_session_in_process(project_root: str, index: int) -> str:
    store = FileMaterialStore(Path(project_root))
    session = store.create_session(
        title=f"Session {index}",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance={"runtime": "codex"},
    )
    return str(session["learnable_session_id"])


def _add_child_in_process(args: tuple[str, str, str, int]) -> str:
    project_root, session_id, root_node_id, index = args
    store = FileMaterialStore(Path(project_root))
    child = store.add_child(
        learnable_session_id=session_id,
        parent_node_id=root_node_id,
        title=f"Child {index}",
        prompt="Child prompt",
        markdown=f"## Child {index}\n",
        provenance={"runtime": "codex"},
    )
    return str(child["node_id"])


def test_file_material_store_implements_public_protocol(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)

    assert isinstance(store, MaterialStore)


def test_init_creates_material_layout_and_server_files(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)

    store.init()

    materials = tmp_path / ".codex" / "materials"
    server = materials / ".server"
    assert json.loads((materials / "index.json").read_text(encoding="utf-8")) == {
        "schema_version": "1.0",
        "sessions": [],
    }
    assert (server / "config.json").is_file()
    assert (server / "token").read_text(encoding="utf-8").strip()
    assert (server / "audits.jsonl").read_text(encoding="utf-8") == ""


def test_create_session_persists_index_session_graph_material_and_markdown(
    tmp_path: Path,
) -> None:
    store = FileMaterialStore(tmp_path)

    session = store.create_session(
        title="Learning path",
        prompt="Explain TOKEN=learnable-token-12345",
        markdown="# Root\n",
        provenance=_provenance(),
        source_refs=[{"source_id": "source-001"}],
    )

    materials = tmp_path / ".codex" / "materials"
    session_id = session["learnable_session_id"]
    root_node_id = session["root_node_id"]
    session_dir = materials / "sessions" / str(session_id)
    node_dir = session_dir / "nodes" / str(root_node_id)
    index = json.loads((materials / "index.json").read_text(encoding="utf-8"))
    material = json.loads((node_dir / "material.json").read_text(encoding="utf-8"))

    assert set(index["sessions"][0]) == {
        "learnable_session_id",
        "title",
        "root_node_id",
        "status",
        "created_at",
        "updated_at",
        "session_json_path",
    }
    assert index["sessions"][0]["learnable_session_id"] == session_id
    assert index["sessions"][0]["session_json_path"] == (
        f"sessions/{session_id}/session.json"
    )
    assert "runtime-session-a" not in json.dumps(index, sort_keys=True)
    assert (session_dir / "session.json").is_file()
    assert (session_dir / "graph.json").is_file()
    assert (session_dir / "events.jsonl").is_file()
    assert material["node_id"] == root_node_id
    assert material["source_refs"] == [{"source_id": "source-001"}]
    assert "learnable-token-12345" not in material["created_from_prompt"]
    assert (node_dir / "node.md").read_text(encoding="utf-8") == "# Root\n"


def test_create_session_preserves_legacy_string_source_refs_in_material_and_load_node(
    tmp_path: Path,
) -> None:
    store = FileMaterialStore(tmp_path)

    session = store.create_session(
        title="Legacy sources",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance=_provenance(),
        source_refs=["legacy-source"],
    )

    material, markdown = store.load_node(
        str(session["learnable_session_id"]),
        str(session["root_node_id"]),
    )
    assert material["source_refs"] == ["legacy-source"]
    assert markdown == "# Root\n"


def test_concurrent_create_session_preserves_all_index_entries(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)

    def create(index: int) -> dict[str, object]:
        return store.create_session(
            title=f"Session {index}",
            prompt="Root prompt",
            markdown="# Root\n",
            provenance=_provenance(),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        sessions = list(executor.map(create, range(20)))

    listed = store.list_sessions()

    assert {item["learnable_session_id"] for item in listed} == {
        session["learnable_session_id"] for session in sessions
    }


def test_multiprocess_create_session_preserves_all_index_entries(
    tmp_path: Path,
) -> None:
    context = get_context("spawn")

    with context.Pool(processes=4) as pool:
        session_ids = pool.starmap(
            _create_session_in_process,
            [(str(tmp_path), index) for index in range(12)],
        )

    listed = FileMaterialStore(tmp_path).list_sessions()

    assert {item["learnable_session_id"] for item in listed} == set(session_ids)


def test_create_session_removes_session_directory_when_session_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FileMaterialStore(tmp_path)
    store.init()
    materials = tmp_path / ".codex" / "materials"

    from learnable.materials import file_store

    original_replace = file_store.os.replace

    def fail_session_replace(src: str | Path, dst: str | Path) -> None:
        if Path(dst).name == "session.json":
            raise OSError("simulated session replace failure")
        original_replace(src, dst)

    monkeypatch.setattr(file_store.os, "replace", fail_session_replace)

    with pytest.raises(OSError, match="simulated session replace failure"):
        store.create_session(
            title="Learning path",
            prompt="Root prompt",
            markdown="# Root\n",
            provenance=_provenance(),
        )

    index = json.loads((materials / "index.json").read_text(encoding="utf-8"))
    assert index["sessions"] == []
    sessions_dir = materials / "sessions"
    assert not sessions_dir.exists() or list(sessions_dir.iterdir()) == []


def test_add_child_updates_tree_and_load_node(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Learning path",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance=_provenance(),
    )

    child = store.add_child(
        learnable_session_id=str(session["learnable_session_id"]),
        parent_node_id=str(session["root_node_id"]),
        title="Child topic",
        prompt="Child prompt",
        markdown="## Child\n",
        provenance=_provenance(),
    )

    tree = store.load_tree(str(session["learnable_session_id"]))
    material, markdown = store.load_node(
        str(session["learnable_session_id"]), str(child["node_id"])
    )
    assert tree["root_node_id"] == session["root_node_id"]
    assert str(child["node_id"]) in tree["nodes"]
    assert material["parent_node_id"] == session["root_node_id"]
    assert material["depth"] == 1
    assert markdown == "## Child\n"


def test_add_child_preserves_legacy_string_and_structured_source_refs(
    tmp_path: Path,
) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Learning path",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance=_provenance(),
    )

    legacy_child = store.add_child(
        learnable_session_id=str(session["learnable_session_id"]),
        parent_node_id=str(session["root_node_id"]),
        title="Legacy child",
        prompt="Child prompt",
        markdown="## Legacy\n",
        provenance=_provenance(),
        source_refs=["legacy-source"],
    )
    structured_child = store.add_child(
        learnable_session_id=str(session["learnable_session_id"]),
        parent_node_id=str(session["root_node_id"]),
        title="Structured child",
        prompt="Child prompt",
        markdown="## Structured\n",
        provenance=_provenance(),
        source_refs=[{"source_id": "source-001", "weight": 1}],
    )

    legacy_material, _ = store.load_node(
        str(session["learnable_session_id"]),
        str(legacy_child["node_id"]),
    )
    structured_material, _ = store.load_node(
        str(session["learnable_session_id"]),
        str(structured_child["node_id"]),
    )
    assert legacy_material["source_refs"] == ["legacy-source"]
    assert structured_material["source_refs"] == [
        {"source_id": "source-001", "weight": 1}
    ]


def test_concurrent_add_child_preserves_graph_and_materials(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Learning path",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance=_provenance(),
    )
    session_id = str(session["learnable_session_id"])
    root_node_id = str(session["root_node_id"])

    def add(index: int) -> dict[str, object]:
        return store.add_child(
            learnable_session_id=session_id,
            parent_node_id=root_node_id,
            title=f"Child {index}",
            prompt="Child prompt",
            markdown=f"## Child {index}\n",
            provenance=_provenance(),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        children = list(executor.map(add, range(20)))

    tree = store.load_tree(session_id)

    assert {str(child["node_id"]) for child in children}.issubset(set(tree["nodes"]))
    assert len(tree["nodes"]) == 21


def test_multiprocess_add_child_preserves_graph_and_materials(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Learning path",
        prompt="Root prompt",
        markdown="# Root\n",
        provenance=_provenance(),
    )
    session_id = str(session["learnable_session_id"])
    root_node_id = str(session["root_node_id"])
    context = get_context("spawn")

    with context.Pool(processes=4) as pool:
        child_ids = pool.map(
            _add_child_in_process,
            [(str(tmp_path), session_id, root_node_id, index) for index in range(12)],
        )

    tree = store.load_tree(session_id)

    assert set(child_ids).issubset(set(tree["nodes"]))
    assert len(tree["nodes"]) == 13


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("depth", 999),
        ("parent_node_id", "node-missing"),
        ("learnable_session_id", "learnable-session-mismatch"),
    ],
)
def test_load_tree_rejects_material_metadata_mismatch(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session("Root", "Prompt", "# Root\n", _provenance())
    child = store.add_child(
        str(session["learnable_session_id"]),
        str(session["root_node_id"]),
        "Child",
        "Prompt",
        "Child",
        _provenance(),
    )
    material_path = (
        tmp_path
        / ".codex"
        / "materials"
        / "sessions"
        / str(session["learnable_session_id"])
        / "nodes"
        / str(child["node_id"])
        / "material.json"
    )
    material = json.loads(material_path.read_text(encoding="utf-8"))
    material[field] = value
    material_path.write_text(json.dumps(material), encoding="utf-8")

    with pytest.raises(ValueError, match="metadata mismatch"):
        store.load_tree(str(session["learnable_session_id"]))


def test_load_tree_rejects_graph_material_path_mismatch(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session("Root", "Prompt", "# Root\n", _provenance())
    child = store.add_child(
        str(session["learnable_session_id"]),
        str(session["root_node_id"]),
        "Child",
        "Prompt",
        "Child",
        _provenance(),
    )
    graph_path = (
        tmp_path
        / ".codex"
        / "materials"
        / "sessions"
        / str(session["learnable_session_id"])
        / "graph.json"
    )
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["nodes"][str(child["node_id"])]["material_path"] = (
        f"sessions/{session['learnable_session_id']}/nodes/node-other/material.json"
    )
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    with pytest.raises(ValueError, match="metadata mismatch"):
        store.load_tree(str(session["learnable_session_id"]))


def test_list_sessions_returns_repository_level_material_session_index(
    tmp_path: Path,
) -> None:
    store = FileMaterialStore(tmp_path)
    first = store.create_session("First", "Prompt", "# First\n", _provenance())
    second = store.create_session("Second", "Prompt", "# Second\n", _provenance())

    sessions = store.list_sessions()

    assert [item["learnable_session_id"] for item in sessions] == [
        first["learnable_session_id"],
        second["learnable_session_id"],
    ]
    assert all("codex_session_id" not in item for item in sessions)


def test_add_child_keeps_previous_valid_graph_when_graph_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session("Root", "Prompt", "# Root\n", _provenance())
    session_id = str(session["learnable_session_id"])
    graph_path = (
        tmp_path / ".codex" / "materials" / "sessions" / session_id / "graph.json"
    )
    before = graph_path.read_text(encoding="utf-8")

    def fail_graph_replace(src: str | Path, dst: str | Path) -> None:
        if Path(dst) == graph_path:
            raise OSError("simulated graph replace failure")
        original_replace(src, dst)

    from learnable.materials import file_store

    original_replace = file_store.os.replace
    monkeypatch.setattr(file_store.os, "replace", fail_graph_replace)

    with pytest.raises(OSError, match="simulated graph replace failure"):
        store.add_child(
            session_id,
            str(session["root_node_id"]),
            "Child",
            "Prompt",
            "Child",
            _provenance(),
        )

    assert graph_path.read_text(encoding="utf-8") == before
    assert len(list((graph_path.parent / "nodes").iterdir())) == 1


def test_add_child_keeps_previous_tree_when_child_file_replace_fails_before_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session("Root", "Prompt", "# Root\n", _provenance())
    session_id = str(session["learnable_session_id"])
    graph_path = (
        tmp_path / ".codex" / "materials" / "sessions" / session_id / "graph.json"
    )
    nodes_path = graph_path.parent / "nodes"
    before_graph = graph_path.read_text(encoding="utf-8")
    before_nodes = sorted(path.name for path in nodes_path.iterdir())

    from learnable.materials import file_store

    original_replace = file_store.os.replace
    graph_replace_before_failure = False
    material_failure_seen = False

    def fail_material_replace_before_graph(
        src: str | Path,
        dst: str | Path,
    ) -> None:
        nonlocal graph_replace_before_failure, material_failure_seen
        dst_path = Path(dst)
        if dst_path == graph_path and not material_failure_seen:
            graph_replace_before_failure = True
        if dst_path.name == "material.json" and dst_path.parent != nodes_path:
            material_failure_seen = True
            raise OSError("simulated child material replace failure")
        original_replace(src, dst)

    monkeypatch.setattr(file_store.os, "replace", fail_material_replace_before_graph)

    with pytest.raises(OSError, match="simulated child material replace failure"):
        store.add_child(
            session_id,
            str(session["root_node_id"]),
            "Child",
            "Prompt",
            "Child",
            _provenance(),
        )

    assert graph_replace_before_failure is False
    assert graph_path.read_text(encoding="utf-8") == before_graph
    assert sorted(path.name for path in nodes_path.iterdir()) == before_nodes
    assert store.load_tree(session_id)["nodes"] == json.loads(before_graph)["nodes"]


def test_atomic_write_text_fsyncs_parent_directory_after_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from learnable.materials import file_store

    target = tmp_path / "record.json"
    directory_fd = 9876
    opened_dirs: list[Path] = []
    fsynced_fds: list[int] = []
    closed_fds: list[int] = []

    original_open = file_store.os.open

    def fake_open(path: str | Path, flags: int, mode: int = 0o777) -> int:
        if Path(path) == tmp_path:
            opened_dirs.append(Path(path))
            assert flags == file_store.os.O_RDONLY
            return directory_fd
        return original_open(path, flags, mode)

    def fake_fsync(fd: int) -> None:
        fsynced_fds.append(fd)

    def fake_close(fd: int) -> None:
        closed_fds.append(fd)

    monkeypatch.setattr(file_store.os, "open", fake_open)
    monkeypatch.setattr(file_store.os, "fsync", fake_fsync)
    monkeypatch.setattr(file_store.os, "close", fake_close)

    file_store._atomic_write_text(target, "content")

    assert target.read_text(encoding="utf-8") == "content"
    assert opened_dirs == [tmp_path]
    assert directory_fd in fsynced_fds
    assert closed_fds == [directory_fd]


def test_add_child_rolls_back_when_event_append_fails_after_graph_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session("Root", "Prompt", "# Root\n", _provenance())
    session_id = str(session["learnable_session_id"])
    graph_path = (
        tmp_path / ".codex" / "materials" / "sessions" / session_id / "graph.json"
    )
    index_path = tmp_path / ".codex" / "materials" / "index.json"
    session_path = graph_path.parent / "session.json"
    nodes_path = graph_path.parent / "nodes"
    before_graph = graph_path.read_text(encoding="utf-8")
    before_index = index_path.read_text(encoding="utf-8")
    before_session = session_path.read_text(encoding="utf-8")
    before_nodes = sorted(path.name for path in nodes_path.iterdir())

    from learnable.materials import file_store

    original_replace = file_store.os.replace
    graph_replaced = False

    def fail_child_file_after_graph_replace(
        src: str | Path,
        dst: str | Path,
    ) -> None:
        nonlocal graph_replaced
        dst_path = Path(dst)
        if dst_path == graph_path:
            graph_replaced = True
        original_replace(src, dst)

    def fail_event_append_after_graph_replace(*args: object, **kwargs: object) -> None:
        assert graph_replaced is True
        raise OSError("simulated event append failure")

    monkeypatch.setattr(file_store.os, "replace", fail_child_file_after_graph_replace)
    monkeypatch.setattr(file_store, "append_event", fail_event_append_after_graph_replace)

    with pytest.raises(OSError, match="simulated event append failure"):
        store.add_child(
            session_id,
            str(session["root_node_id"]),
            "Child",
            "Prompt",
            "Child",
            _provenance(),
        )

    assert graph_path.read_text(encoding="utf-8") == before_graph
    assert index_path.read_text(encoding="utf-8") == before_index
    assert session_path.read_text(encoding="utf-8") == before_session
    assert sorted(path.name for path in nodes_path.iterdir()) == before_nodes
