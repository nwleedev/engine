from __future__ import annotations

import pytest

from learnable.materials.graph import GraphValidationError, validate_graph_integrity


def _graph(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "1.0",
        "learnable_session_id": "learnable-session-001",
        "root_node_id": "node-root",
        "nodes": {
            "node-root": {
                "node_id": "node-root",
                "parent_node_id": None,
                "depth": 0,
                "material_path": "sessions/learnable-session-001/nodes/node-root/material.json",
            },
            "node-child": {
                "node_id": "node-child",
                "parent_node_id": "node-root",
                "depth": 1,
                "material_path": "sessions/learnable-session-001/nodes/node-child/material.json",
            },
        },
        "edges": [{"parent_node_id": "node-root", "node_id": "node-child"}],
        "created_at": "2026-05-18T09:00:00Z",
        "updated_at": "2026-05-18T09:01:00Z",
        "provenance": {"runtime": "codex"},
    }
    data.update(overrides)
    return data


def test_validate_graph_integrity_accepts_single_root_tree() -> None:
    validate_graph_integrity(_graph(), material_node_ids={"node-root", "node-child"})


def test_validate_graph_integrity_rejects_canonical_field_metadata_mismatch() -> None:
    materials = {
        "node-root": {
            "learnable_session_id": "learnable-session-001",
            "node_id": "node-root",
            "parent_node_id": None,
            "depth": 0,
        },
        "node-child": {
            "learnable_session_id": "learnable-session-001",
            "node_id": "node-child",
            "parent_node_id": "node-root",
            "depth": 999,
        },
    }

    with pytest.raises(
        GraphValidationError,
        match="canonical metadata field mismatch: depth",
    ):
        validate_graph_integrity(
            _graph(),
            material_node_ids={"node-root", "node-child"},
            material_records_by_node=materials,
        )


def test_validate_graph_integrity_reports_canonical_metadata_completeness_scope() -> None:
    materials = {
        "node-root": {
            "learnable_session_id": "learnable-session-001",
            "node_id": "node-root",
            "parent_node_id": None,
            "depth": 0,
        },
        "node-child": {
            "learnable_session_id": "learnable-session-001",
            "node_id": "node-child",
            "parent_node_id": "node-root",
            "depth": 1,
        },
    }
    graph = _graph()
    graph["nodes"]["node-child"]["material_path"] = "sessions/wrong/material.json"

    with pytest.raises(
        GraphValidationError,
        match=(
            "canonical metadata fields: node_id, parent_node_id, depth, "
            "learnable_session_id, material_path"
        ),
    ):
        validate_graph_integrity(
            graph,
            material_node_ids={"node-root", "node-child"},
            material_records_by_node=materials,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "edges": [
                    {"parent_node_id": "node-missing", "node_id": "node-child"},
                ]
            },
            "missing parent",
        ),
        (
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-duplicate",
                        "parent_node_id": None,
                        "depth": 0,
                    },
                    "node-child": {
                        "node_id": "node-duplicate",
                        "parent_node_id": "node-root",
                        "depth": 1,
                    },
                }
            },
            "duplicate node id",
        ),
        (
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-root",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": "sessions/learnable-session-001/nodes/node-root/material.json",
                    },
                    "node-other": {
                        "node_id": "node-other",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": "sessions/learnable-session-001/nodes/node-other/material.json",
                    },
                },
                "edges": [],
            },
            "multiple roots",
        ),
        (
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-root",
                        "parent_node_id": "node-child",
                        "depth": 0,
                        "material_path": "sessions/learnable-session-001/nodes/node-root/material.json",
                    },
                    "node-child": {
                        "node_id": "node-child",
                        "parent_node_id": "node-root",
                        "depth": 1,
                        "material_path": "sessions/learnable-session-001/nodes/node-child/material.json",
                    },
                }
            },
            "cycle",
        ),
        (
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-root",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": "sessions/learnable-session-001/nodes/node-root/material.json",
                    },
                    "node-child": {
                        "node_id": "node-child",
                        "parent_node_id": "node-root",
                        "depth": 3,
                        "material_path": "sessions/learnable-session-001/nodes/node-child/material.json",
                    },
                }
            },
            "invalid depth",
        ),
        (
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-root",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": "sessions/learnable-session-001/nodes/node-root/material.json",
                    },
                    "node-child": {
                        "node_id": "node-child",
                        "parent_node_id": "node-root",
                        "depth": 1,
                        "material_path": "sessions/learnable-session-001/nodes/node-child/material.json",
                    },
                }
            },
            "depth limit",
        ),
        (
            {
                "edges": [
                    {"parent_node_id": "node-root", "node_id": "node-child"},
                    {"parent_node_id": "node-root", "node_id": "node-child"},
                ]
            },
            "duplicate edge",
        ),
    ],
)
def test_validate_graph_integrity_rejects_invalid_graphs(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(GraphValidationError, match=message):
        validate_graph_integrity(
            _graph(**overrides),
            material_node_ids={"node-root", "node-child"},
            max_depth=0 if message == "depth limit" else 20,
        )


def test_validate_graph_integrity_rejects_graph_node_without_material_metadata() -> None:
    with pytest.raises(GraphValidationError, match="metadata missing"):
        validate_graph_integrity(_graph(), material_node_ids={"node-root"})


def test_validate_graph_integrity_rejects_material_metadata_without_graph_node() -> None:
    with pytest.raises(GraphValidationError, match="metadata missing"):
        validate_graph_integrity(
            _graph(),
            material_node_ids={"node-root", "node-child", "node-orphan"},
        )
