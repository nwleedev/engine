from __future__ import annotations

import json

import pytest

from learnable.materials.schemas import SchemaValidationError, load_schema_resource


def test_load_schema_resource_rejects_unknown_names() -> None:
    with pytest.raises(SchemaValidationError, match="unknown"):
        load_schema_resource("../session.schema.json")


def test_schema_resources_are_parseable_json_objects() -> None:
    for name in ("session.schema.json", "material.schema.json", "graph.schema.json"):
        schema = json.loads(load_schema_resource(name))

        assert schema["type"] == "object"
        assert isinstance(schema["properties"], dict)


def test_json_schema_files_document_provenance_constraints() -> None:
    for name in ("session.schema.json", "material.schema.json", "graph.schema.json"):
        schema = json.loads(load_schema_resource(name))
        provenance = schema["properties"]["provenance"]

        assert provenance["additionalProperties"] is False
        assert provenance["properties"]["runtime"]["enum"] == [
            "codex",
            "claude",
            "unknown",
        ]


def test_material_schema_documents_runtime_ids_are_not_identity_fields() -> None:
    schema = json.loads(load_schema_resource("material.schema.json"))

    assert schema["not"]["anyOf"] == [
        {"required": ["codex_thread_id"]},
        {"required": ["codex_session_id"]},
        {"required": ["codex_turn_id"]},
        {"required": ["app_server_thread_id"]},
    ]


def test_session_schema_documents_runtime_ids_are_not_root_node_identity() -> None:
    schema = json.loads(load_schema_resource("session.schema.json"))

    assert schema["x-learnable-rules"] == [
        (
            "provenance runtime id values must not be used as "
            "learnable_session_id or root_node_id"
        )
    ]


def test_material_schema_documents_runtime_ids_are_not_graph_identity_values() -> None:
    schema = json.loads(load_schema_resource("material.schema.json"))

    assert schema["x-learnable-rules"] == [
        (
            "provenance runtime id values must not be used as "
            "learnable_session_id, node_id, or parent_node_id"
        )
    ]


def test_graph_schema_documents_runtime_ids_are_not_session_or_graph_identity() -> None:
    schema = json.loads(load_schema_resource("graph.schema.json"))

    assert schema["x-learnable-rules"] == [
        (
            "provenance runtime id values must not be used as "
            "learnable_session_id, root_node_id, node ids, edge ids, or material_path parts"
        )
    ]


def test_material_schema_allows_null_parent_node_id_for_root_material() -> None:
    schema = json.loads(load_schema_resource("material.schema.json"))

    assert schema["properties"]["parent_node_id"] == {
        "anyOf": [{"type": "string"}, {"type": "null"}]
    }


def test_material_schema_documents_backward_compatible_source_refs() -> None:
    schema = json.loads(load_schema_resource("material.schema.json"))

    assert schema["properties"]["source_refs"] == {
        "type": "array",
        "items": {"anyOf": [{"type": "string"}, {"type": "object"}]},
    }


def test_graph_schema_material_path_description_matches_validator_scope() -> None:
    schema = json.loads(load_schema_resource("graph.schema.json"))
    material_path = schema["properties"]["nodes"]["additionalProperties"]["properties"][
        "material_path"
    ]

    assert material_path["description"] == (
        "Path parts must not use runtime provenance ids."
    )


def test_graph_schema_requires_persisted_node_metadata_fields() -> None:
    schema = json.loads(load_schema_resource("graph.schema.json"))
    node_schema = schema["properties"]["nodes"]["additionalProperties"]

    assert node_schema["required"] == [
        "node_id",
        "parent_node_id",
        "depth",
        "material_path",
    ]
    assert node_schema["properties"]["depth"] == {"type": "integer"}
