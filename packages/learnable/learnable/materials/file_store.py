from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from collections.abc import Mapping
from contextlib import contextmanager, suppress
from pathlib import Path

from learnable.core.config import default_server_config, write_server_config
from learnable.core.paths import ensure_within_root, materials_root
from learnable.core.redaction import redact_text
from learnable.materials.events import append_event, utc_now
from learnable.materials.graph import validate_graph_integrity
from learnable.materials.schemas import (
    validate_graph_record,
    validate_material_record,
    validate_provenance,
    validate_session_record,
)

type SourceRefs = list[str | dict[str, object]] | None


class FileMaterialStore:
    """File-backed Learnable material store under `.codex/materials`."""

    def __init__(self, project_root: Path, *, max_depth: int = 20) -> None:
        self.project_root = project_root.resolve()
        self.max_depth = max_depth

    def init(self) -> None:
        lock_path = self.project_root / ".codex" / "materials" / ".server" / "store.lock"
        with _file_lock(lock_path):
            root = materials_root(self.project_root)
            write_server_config(
                self.project_root,
                default_server_config(self.project_root),
            )
            index_path = root / "index.json"
            if not index_path.exists():
                _atomic_write_json(index_path, {"schema_version": "1.0", "sessions": []})

    def create_session(
        self,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs = None,
    ) -> dict[str, object]:
        self.init()
        lock_path = self.project_root / ".codex" / "materials" / ".server" / "store.lock"
        with _file_lock(lock_path):
            return self._create_session_locked(
                title,
                prompt,
                markdown,
                provenance,
                source_refs,
            )

    def _create_session_locked(
        self,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs,
    ) -> dict[str, object]:
        validate_provenance(provenance)
        created_at = utc_now()
        learnable_session_id = _new_id("learnable-session")
        root_node_id = _new_id("node")
        session_dir = self._session_dir(learnable_session_id)
        node_dir = self._node_dir(learnable_session_id, root_node_id)
        index_before = self._index_path().read_text(encoding="utf-8")
        session_dir.mkdir(parents=True, exist_ok=True)
        node_dir.mkdir(parents=True, exist_ok=True)

        session = {
            "schema_version": "1.0",
            "learnable_session_id": learnable_session_id,
            "title": title,
            "root_node_id": root_node_id,
            "status": "active",
            "created_at": created_at,
            "updated_at": created_at,
            "provenance": dict(provenance),
        }
        material = _material_record(
            learnable_session_id=learnable_session_id,
            node_id=root_node_id,
            parent_node_id=None,
            title=title,
            depth=0,
            prompt=prompt,
            created_at=created_at,
            provenance=provenance,
            source_refs=source_refs,
        )
        graph = _graph_record(
            learnable_session_id=learnable_session_id,
            root_node_id=root_node_id,
            nodes={
                root_node_id: _graph_node(
                    learnable_session_id, root_node_id, None, 0
                )
            },
            edges=[],
            created_at=created_at,
            updated_at=created_at,
            provenance=provenance,
        )
        self._validate_records(session, graph, {root_node_id: material})

        try:
            _atomic_write_json(session_dir / "graph.json", graph)
            _atomic_write_json(node_dir / "material.json", material)
            _atomic_write_text(node_dir / "node.md", markdown)
            _atomic_write_json(session_dir / "session.json", session)
            _atomic_write_text(session_dir / "events.jsonl", "")
            self._write_index_with_session(session)
            append_event(
                session_dir / "events.jsonl",
                event_type="session.created",
                learnable_session_id=learnable_session_id,
                node_id=root_node_id,
                message=f"created session {title}",
            )
        except Exception:
            shutil.rmtree(session_dir, ignore_errors=True)
            with suppress(Exception):
                _atomic_write_text(self._index_path(), index_before)
            raise
        return dict(session)

    def add_child(
        self,
        learnable_session_id: str,
        parent_node_id: str,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs = None,
    ) -> dict[str, object]:
        lock_path = self.project_root / ".codex" / "materials" / ".server" / "store.lock"
        with _file_lock(lock_path):
            return self._add_child_locked(
                learnable_session_id,
                parent_node_id,
                title,
                prompt,
                markdown,
                provenance,
                source_refs,
            )

    def _add_child_locked(
        self,
        learnable_session_id: str,
        parent_node_id: str,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs,
    ) -> dict[str, object]:
        validate_provenance(provenance)
        session_dir = self._session_dir(learnable_session_id)
        session_path = session_dir / "session.json"
        graph_path = session_dir / "graph.json"
        index_path = self._index_path()
        session_before = session_path.read_text(encoding="utf-8")
        graph_before = graph_path.read_text(encoding="utf-8")
        index_before = index_path.read_text(encoding="utf-8")
        session = _read_json(session_path)
        graph = _read_json(graph_path)
        nodes = graph["nodes"]
        if not isinstance(nodes, dict):
            raise ValueError("graph nodes must be an object")
        parent = nodes.get(parent_node_id)
        if not isinstance(parent, Mapping):
            raise ValueError("parent node does not exist")
        parent_depth = parent.get("depth")
        if not isinstance(parent_depth, int):
            raise ValueError("parent depth is invalid")
        depth = parent_depth + 1
        node_id = _new_id("node")
        created_at = utc_now()

        material = _material_record(
            learnable_session_id=learnable_session_id,
            node_id=node_id,
            parent_node_id=parent_node_id,
            title=title,
            depth=depth,
            prompt=prompt,
            created_at=created_at,
            provenance=provenance,
            source_refs=source_refs,
        )
        next_graph = dict(graph)
        next_nodes = dict(nodes)
        next_nodes[node_id] = _graph_node(
            learnable_session_id, node_id, parent_node_id, depth
        )
        next_edges = list(graph["edges"]) if isinstance(graph["edges"], list) else []
        next_edges.append({"parent_node_id": parent_node_id, "node_id": node_id})
        next_graph["nodes"] = next_nodes
        next_graph["edges"] = next_edges
        next_graph["updated_at"] = created_at
        session["updated_at"] = created_at
        self._validate_records(
            session,
            next_graph,
            self._materials_by_node(learnable_session_id) | {node_id: material},
        )

        node_dir = self._node_dir(learnable_session_id, node_id)
        try:
            _atomic_write_json(node_dir / "material.json", material)
            _atomic_write_text(node_dir / "node.md", markdown)
            _atomic_write_json(session_path, session)
            self._replace_index_entry(session)
            _atomic_write_json(graph_path, next_graph)
            append_event(
                session_dir / "events.jsonl",
                event_type="node.created",
                learnable_session_id=learnable_session_id,
                node_id=node_id,
                message=f"created node {title}",
            )
        except Exception:
            shutil.rmtree(node_dir, ignore_errors=True)
            with suppress(Exception):
                _atomic_write_text(graph_path, graph_before)
            with suppress(Exception):
                _atomic_write_text(session_path, session_before)
            with suppress(Exception):
                _atomic_write_text(index_path, index_before)
            raise
        return dict(material)

    def load_tree(self, learnable_session_id: str) -> dict[str, object]:
        graph = _read_json(self._session_dir(learnable_session_id) / "graph.json")
        materials = self._materials_by_node(learnable_session_id)
        validate_graph_integrity(
            graph,
            material_node_ids=set(materials),
            material_records_by_node=materials,
            max_depth=self.max_depth,
        )
        return graph

    def load_node(
        self, learnable_session_id: str, node_id: str
    ) -> tuple[dict[str, object], str]:
        node_dir = self._node_dir(learnable_session_id, node_id)
        material = _read_json(node_dir / "material.json")
        validate_material_record(material)
        markdown = (node_dir / "node.md").read_text(encoding="utf-8")
        return material, markdown

    def list_sessions(self) -> list[dict[str, object]]:
        self.init()
        index = _read_json(self._index_path())
        sessions = index.get("sessions", [])
        if not isinstance(sessions, list):
            raise ValueError("material index sessions must be a list")
        return [dict(item) for item in sessions if isinstance(item, Mapping)]

    def _validate_records(
        self,
        session: Mapping[str, object],
        graph: Mapping[str, object],
        materials: Mapping[str, Mapping[str, object]],
    ) -> None:
        validate_session_record(session)
        validate_graph_record(graph)
        for material in materials.values():
            validate_material_record(material)
        validate_graph_integrity(
            graph,
            material_node_ids=set(materials),
            material_records_by_node=materials,
            max_depth=self.max_depth,
        )

    def _write_index_with_session(self, session: Mapping[str, object]) -> None:
        index = _read_json(self._index_path())
        sessions = index.get("sessions")
        if not isinstance(sessions, list):
            sessions = []
        sessions.append(_index_entry(session))
        index["sessions"] = sessions
        _atomic_write_json(self._index_path(), index)

    def _replace_index_entry(self, session: Mapping[str, object]) -> None:
        index = _read_json(self._index_path())
        sessions = index.get("sessions")
        if not isinstance(sessions, list):
            raise ValueError("material index sessions must be a list")
        session_id = session["learnable_session_id"]
        index["sessions"] = [
            _index_entry(session) if item.get("learnable_session_id") == session_id else item
            for item in sessions
            if isinstance(item, Mapping)
        ]
        _atomic_write_json(self._index_path(), index)

    def _materials_by_node(
        self, learnable_session_id: str
    ) -> dict[str, Mapping[str, object]]:
        nodes_root = self._session_dir(learnable_session_id) / "nodes"
        materials: dict[str, Mapping[str, object]] = {}
        if not nodes_root.exists():
            return materials
        for material_path in nodes_root.glob("*/material.json"):
            material = _read_json(material_path)
            node_id = material.get("node_id")
            if isinstance(node_id, str):
                materials[node_id] = material
        return materials

    def _index_path(self) -> Path:
        return ensure_within_root(
            self.project_root / ".codex" / "materials" / "index.json",
            self.project_root,
        )

    def _session_dir(self, learnable_session_id: str) -> Path:
        return ensure_within_root(
            (
                self.project_root
                / ".codex"
                / "materials"
                / "sessions"
                / learnable_session_id
            ),
            self.project_root,
        )

    def _node_dir(self, learnable_session_id: str, node_id: str) -> Path:
        return ensure_within_root(
            self._session_dir(learnable_session_id) / "nodes" / node_id,
            self.project_root,
        )


def _graph_record(
    *,
    learnable_session_id: str,
    root_node_id: str,
    nodes: Mapping[str, object],
    edges: list[dict[str, str]],
    created_at: str,
    updated_at: str,
    provenance: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "learnable_session_id": learnable_session_id,
        "root_node_id": root_node_id,
        "nodes": dict(nodes),
        "edges": edges,
        "created_at": created_at,
        "updated_at": updated_at,
        "provenance": dict(provenance),
    }


def _graph_node(
    learnable_session_id: str,
    node_id: str,
    parent_node_id: str | None,
    depth: int,
) -> dict[str, object]:
    return {
        "node_id": node_id,
        "parent_node_id": parent_node_id,
        "depth": depth,
        "material_path": (
            f"sessions/{learnable_session_id}/nodes/{node_id}/material.json"
        ),
    }


def _material_record(
    *,
    learnable_session_id: str,
    node_id: str,
    parent_node_id: str | None,
    title: str,
    depth: int,
    prompt: str,
    created_at: str,
    provenance: Mapping[str, object],
    source_refs: SourceRefs,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "learnable_session_id": learnable_session_id,
        "node_id": node_id,
        "parent_node_id": parent_node_id,
        "title": title,
        "depth": depth,
        "status": "draft",
        "source_refs": _source_refs(source_refs),
        "created_from_prompt": redact_text(prompt),
        "created_at": created_at,
        "updated_at": created_at,
        "provenance": dict(provenance),
    }


def _index_entry(session: Mapping[str, object]) -> dict[str, object]:
    learnable_session_id = str(session["learnable_session_id"])
    return {
        "learnable_session_id": learnable_session_id,
        "title": session["title"],
        "root_node_id": session["root_node_id"],
        "status": session["status"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "session_json_path": f"sessions/{learnable_session_id}/session.json",
    }


def _source_refs(
    source_refs: SourceRefs,
) -> list[str | dict[str, object]]:
    if source_refs is None:
        return []
    return [item if isinstance(item, str) else dict(item) for item in source_refs]


def _read_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object JSON at {path}")
    return data


def _atomic_write_json(path: Path, data: Mapping[str, object]) -> None:
    _atomic_write_text(
        path,
        json.dumps(data, indent=2, sort_keys=True) + "\n",
    )


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_parent_dir(path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _fsync_parent_dir(path: Path) -> None:
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


@contextmanager
def _file_lock(path: Path):
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"
