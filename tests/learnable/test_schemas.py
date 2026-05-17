from __future__ import annotations

import json
from collections.abc import Mapping

import pytest

from learnable.materials.schemas import (
    SchemaValidationError,
    load_schema_resource,
    validate_graph_record,
    validate_material_record,
    validate_session_record,
)


def _provenance(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {"runtime": "codex"}
    data.update(overrides)
    return data


def _session_record(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "1.0",
        "learnable_session_id": "learnable-session-001",
        "title": "Learning path",
        "root_node_id": "node-root",
        "status": "active",
        "created_at": "2026-05-18T09:00:00Z",
        "updated_at": "2026-05-18T09:30:00Z",
        "provenance": _provenance(codex_session_id="runtime-session-a"),
    }
    data.update(overrides)
    return data


def _material_record(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "1.0",
        "learnable_session_id": "learnable-session-001",
        "node_id": "node-child",
        "parent_node_id": "node-root",
        "title": "Topic note",
        "depth": 1,
        "status": "draft",
        "source_refs": [{"source_id": "source-001"}],
        "created_from_prompt": "Explain the topic.",
        "created_at": "2026-05-18T09:00:00Z",
        "updated_at": "2026-05-18T09:30:00Z",
    }
    data.update(overrides)
    return data


def _graph_record(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": "1.0",
        "learnable_session_id": "learnable-session-001",
        "root_node_id": "node-root",
        "nodes": {
            "node-root": {
                "node_id": "node-root",
                "parent_node_id": None,
                "depth": 0,
                "material_path": (
                    "sessions/learnable-session-001/nodes/node-root/material.json"
                ),
            },
            "node-child": {
                "node_id": "node-child",
                "parent_node_id": "node-root",
                "depth": 1,
                "material_path": (
                    "sessions/learnable-session-001/nodes/node-child/material.json"
                ),
            },
        },
        "edges": [{"parent_node_id": "node-root", "node_id": "node-child"}],
        "created_at": "2026-05-18T09:00:00Z",
        "updated_at": "2026-05-18T09:30:00Z",
        "provenance": _provenance(codex_thread_id="runtime-thread-a"),
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    ("validator", "record_factory", "required_field"),
    [
        (validate_session_record, _session_record, "learnable_session_id"),
        (validate_material_record, _material_record, "source_refs"),
        (validate_graph_record, _graph_record, "nodes"),
    ],
)
def test_record_validators_require_documented_fields(
    validator: object,
    record_factory: object,
    required_field: str,
) -> None:
    record = record_factory()  # type: ignore[operator]
    validator(record)  # type: ignore[operator]

    del record[required_field]

    with pytest.raises(SchemaValidationError, match=required_field):
        validator(record)  # type: ignore[operator]


def test_material_record_rejects_runtime_ids_as_identity_fields() -> None:
    record = _material_record(codex_session_id="runtime-session-a")

    with pytest.raises(SchemaValidationError, match="codex_session_id"):
        validate_material_record(record)


def test_session_record_rejects_runtime_id_as_root_node_id() -> None:
    record = _session_record(
        root_node_id="runtime-session-a",
        provenance=_provenance(codex_session_id="runtime-session-a"),
    )

    with pytest.raises(SchemaValidationError, match="root_node_id"):
        validate_session_record(record)


def test_session_record_rejects_runtime_id_as_learnable_session_id() -> None:
    record = _session_record(
        learnable_session_id="runtime-session-a",
        provenance=_provenance(codex_session_id="runtime-session-a"),
    )

    with pytest.raises(SchemaValidationError, match="learnable_session_id"):
        validate_session_record(record)


@pytest.mark.parametrize(
    "provenance",
    [
        {"runtime": "local-shell"},
        {"runtime": "codex", "extra": "not-allowed"},
    ],
)
def test_material_record_validates_optional_provenance(
    provenance: dict[str, object],
) -> None:
    record = _material_record(provenance=provenance)

    with pytest.raises(SchemaValidationError, match="runtime|extra"):
        validate_material_record(record)


def test_material_record_accepts_null_parent_node_id_for_root_material() -> None:
    validate_material_record(_material_record(node_id="node-root", parent_node_id=None))


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        ("node_id", {"node_id": "runtime-session-a"}),
        ("parent_node_id", {"parent_node_id": "runtime-session-a"}),
    ],
)
def test_material_record_rejects_runtime_ids_as_graph_identity_values(
    field_name: str,
    overrides: dict[str, object],
) -> None:
    record = _material_record(
        provenance=_provenance(codex_session_id="runtime-session-a"),
        **overrides,
    )

    with pytest.raises(SchemaValidationError, match=field_name):
        validate_material_record(record)


def test_material_record_rejects_runtime_id_as_learnable_session_id() -> None:
    record = _material_record(
        learnable_session_id="runtime-session-a",
        provenance=_provenance(codex_session_id="runtime-session-a"),
    )

    with pytest.raises(SchemaValidationError, match="learnable_session_id"):
        validate_material_record(record)


def test_material_record_rejects_tuple_source_refs() -> None:
    record = _material_record(source_refs=("source-001",))

    with pytest.raises(SchemaValidationError, match="source_refs"):
        validate_material_record(record)


def test_material_record_accepts_legacy_string_source_refs() -> None:
    record = _material_record(source_refs=["source-001"])

    validate_material_record(record)


def test_material_record_accepts_structured_source_refs() -> None:
    record = _material_record(source_refs=[{"source_id": "source-001"}])

    validate_material_record(record)


def test_material_record_rejects_unsupported_source_ref_items() -> None:
    record = _material_record(source_refs=[123])

    with pytest.raises(SchemaValidationError, match="source_refs"):
        validate_material_record(record)


def test_graph_record_uses_node_ids_for_node_lookup_keys() -> None:
    record = _graph_record(
        nodes={
            "runtime-session-a": {
                "node_id": "node-root",
                "parent_node_id": None,
                "depth": 0,
                "material_path": (
                    "sessions/learnable-session-001/nodes/node-root/material.json"
                ),
            }
        },
        provenance=_provenance(codex_session_id="runtime-session-a"),
    )

    with pytest.raises(SchemaValidationError, match="runtime id|node_id"):
        validate_graph_record(record)


def test_graph_record_rejects_runtime_id_as_learnable_session_id() -> None:
    record = _graph_record(
        learnable_session_id="runtime-session-a",
        provenance=_provenance(codex_session_id="runtime-session-a"),
    )

    with pytest.raises(SchemaValidationError, match="learnable_session_id"):
        validate_graph_record(record)


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        ("root_node_id", {"root_node_id": "runtime-session-a"}),
        (
            "node.node_id",
            {
                "nodes": {
                    "node-root": {
                        "node_id": "runtime-session-a",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": (
                            "sessions/learnable-session-001/nodes/node-root/material.json"
                        ),
                    }
                }
            },
        ),
        (
            "node.parent_node_id",
            {
                "nodes": {
                    "node-root": {
                        "node_id": "node-root",
                        "parent_node_id": None,
                        "depth": 0,
                        "material_path": (
                            "sessions/learnable-session-001/nodes/node-root/material.json"
                        ),
                    },
                    "node-child": {
                        "node_id": "node-child",
                        "parent_node_id": "runtime-session-a",
                        "depth": 1,
                        "material_path": (
                            "sessions/learnable-session-001/nodes/node-child/material.json"
                        ),
                    },
                }
            },
        ),
        (
            "edge.parent_node_id",
            {"edges": [{"parent_node_id": "runtime-session-a", "node_id": "node-child"}]},
        ),
        (
            "edge.node_id",
            {"edges": [{"parent_node_id": "node-root", "node_id": "runtime-session-a"}]},
        ),
    ],
)
def test_graph_record_rejects_runtime_ids_in_identity_fields(
    field_name: str,
    overrides: dict[str, object],
) -> None:
    record = _graph_record(
        provenance=_provenance(codex_session_id="runtime-session-a"),
        **overrides,
    )

    with pytest.raises(SchemaValidationError, match=field_name):
        validate_graph_record(record)


def test_graph_record_rejects_tuple_edges() -> None:
    record = _graph_record(edges=({"parent_node_id": "node-root", "node_id": "node-child"},))

    with pytest.raises(SchemaValidationError, match="edges"):
        validate_graph_record(record)


@pytest.mark.parametrize("field_name", ["depth", "material_path"])
def test_graph_record_requires_persisted_node_metadata_fields(field_name: str) -> None:
    record = _graph_record()
    del record["nodes"]["node-child"][field_name]

    with pytest.raises(SchemaValidationError, match=field_name):
        validate_graph_record(record)


def test_graph_record_rejects_invalid_node_depth_type() -> None:
    record = _graph_record()
    record["nodes"]["node-child"]["depth"] = True

    with pytest.raises(SchemaValidationError, match="depth"):
        validate_graph_record(record)


def test_schema_resources_are_json_objects_with_required_metadata() -> None:
    for name in ("session.schema.json", "material.schema.json", "graph.schema.json"):
        schema: Mapping[str, object] = json.loads(load_schema_resource(name))

        assert schema["type"] == "object"
        assert "required" in schema
        assert "provenance" in json.dumps(schema)
