from __future__ import annotations

from collections.abc import Mapping, Sequence
from importlib import resources
from pathlib import PurePosixPath
from typing import Any

from learnable.core.errors import LearnableError


class SchemaValidationError(LearnableError, ValueError):
    """Raised when a Learnable record does not match its schema contract."""


_SCHEMA_RESOURCE_NAMES = {
    "graph.schema.json",
    "material.schema.json",
    "session.schema.json",
}
_PROVENANCE_FIELDS = {
    "runtime",
    "codex_thread_id",
    "codex_session_id",
    "codex_turn_id",
    "app_server_thread_id",
    "diagnostics",
}
_PROVENANCE_RUNTIME_IDS = {
    "codex_thread_id",
    "codex_session_id",
    "codex_turn_id",
    "app_server_thread_id",
}
_RUNTIMES = {"codex", "claude", "unknown"}
_SESSION_REQUIRED = (
    "schema_version",
    "learnable_session_id",
    "title",
    "root_node_id",
    "status",
    "created_at",
    "updated_at",
    "provenance",
)
_MATERIAL_REQUIRED = (
    "schema_version",
    "learnable_session_id",
    "node_id",
    "parent_node_id",
    "title",
    "depth",
    "status",
    "source_refs",
    "created_from_prompt",
    "created_at",
    "updated_at",
)
_GRAPH_REQUIRED = (
    "schema_version",
    "learnable_session_id",
    "root_node_id",
    "nodes",
    "edges",
    "created_at",
    "updated_at",
    "provenance",
)


def load_schema_resource(name: str) -> str:
    if name not in _SCHEMA_RESOURCE_NAMES:
        raise SchemaValidationError(f"unknown schema resource: {name}")
    return (
        resources.files("learnable")
        .joinpath("schemas", name)
        .read_text(encoding="utf-8")
    )


def validate_session_record(data: Mapping[str, object]) -> None:
    record = _require_mapping(data, "session record")
    _require_fields(record, _SESSION_REQUIRED)
    _require_string_fields(
        record,
        (
            "schema_version",
            "learnable_session_id",
            "title",
            "root_node_id",
            "status",
            "created_at",
            "updated_at",
        ),
    )
    provenance = _require_mapping(record["provenance"], "provenance")
    validate_provenance(provenance)
    runtime_ids = _runtime_id_values(provenance)
    _reject_runtime_identity_value(
        record["learnable_session_id"],
        runtime_ids,
        "learnable_session_id",
    )
    _reject_runtime_identity_value(
        record["root_node_id"],
        runtime_ids,
        "root_node_id",
    )


def validate_material_record(data: Mapping[str, object]) -> None:
    record = _require_mapping(data, "material record")
    _require_fields(record, _MATERIAL_REQUIRED)
    _reject_runtime_identity_keys(record)
    _require_string_fields(
        record,
        (
            "schema_version",
            "learnable_session_id",
            "node_id",
            "title",
            "status",
            "created_from_prompt",
            "created_at",
            "updated_at",
        ),
    )
    _require_optional_string(record["parent_node_id"], "parent_node_id")
    if not isinstance(record["depth"], int) or isinstance(record["depth"], bool):
        raise SchemaValidationError("depth must be an integer")
    _require_string_sequence(record["source_refs"], "source_refs")
    if "provenance" in record:
        provenance = _require_mapping(record["provenance"], "provenance")
        validate_provenance(provenance)
        runtime_ids = _runtime_id_values(provenance)
        _reject_runtime_identity_value(
            record["learnable_session_id"],
            runtime_ids,
            "learnable_session_id",
        )
        _reject_runtime_identity_value(record["node_id"], runtime_ids, "node_id")
        parent_node_id = record["parent_node_id"]
        if isinstance(parent_node_id, str):
            _reject_runtime_identity_value(
                parent_node_id,
                runtime_ids,
                "parent_node_id",
            )


def validate_graph_record(data: Mapping[str, object]) -> None:
    record = _require_mapping(data, "graph record")
    _require_fields(record, _GRAPH_REQUIRED)
    _require_string_fields(
        record,
        (
            "schema_version",
            "learnable_session_id",
            "root_node_id",
            "created_at",
            "updated_at",
        ),
    )
    provenance = _require_mapping(record["provenance"], "provenance")
    validate_provenance(provenance)
    runtime_ids = _runtime_id_values(provenance)
    _reject_runtime_identity_value(
        record["learnable_session_id"],
        runtime_ids,
        "learnable_session_id",
    )
    _reject_runtime_identity_value(
        record["root_node_id"],
        runtime_ids,
        "root_node_id",
    )
    nodes = _require_mapping(record["nodes"], "nodes")
    for lookup_key, node_value in nodes.items():
        if not isinstance(lookup_key, str):
            raise SchemaValidationError("node lookup key must be a string")
        _reject_runtime_identity_value(lookup_key, runtime_ids, "node lookup key")
        node = _require_mapping(node_value, f"node {lookup_key}")
        node_id = node.get("node_id")
        if not isinstance(node_id, str):
            raise SchemaValidationError("node.node_id must be a string")
        _reject_runtime_identity_value(node_id, runtime_ids, "node.node_id")
        if node_id != lookup_key:
            raise SchemaValidationError("node lookup key must match node_id")
        parent_node_id = node.get("parent_node_id")
        if parent_node_id is not None and not isinstance(parent_node_id, str):
            raise SchemaValidationError("parent_node_id must be a string or null")
        if isinstance(parent_node_id, str):
            _reject_runtime_identity_value(
                parent_node_id,
                runtime_ids,
                "node.parent_node_id",
            )
        material_path = node.get("material_path")
        if material_path is not None:
            if not isinstance(material_path, str):
                raise SchemaValidationError("material_path must be a string")
            _reject_runtime_path_part(material_path, runtime_ids)
    _require_edges(record["edges"], runtime_ids)


def validate_provenance(data: Mapping[str, object]) -> None:
    provenance = _require_mapping(data, "provenance")
    unknown = sorted(set(provenance) - _PROVENANCE_FIELDS)
    if unknown:
        raise SchemaValidationError(f"unknown provenance fields: {', '.join(unknown)}")
    runtime = provenance.get("runtime")
    if runtime is not None and runtime not in _RUNTIMES:
        raise SchemaValidationError("runtime must be codex, claude, or unknown")
    for field in _PROVENANCE_RUNTIME_IDS:
        value = provenance.get(field)
        if value is not None and not isinstance(value, str):
            raise SchemaValidationError(f"{field} must be a string")
    diagnostics = provenance.get("diagnostics")
    if diagnostics is not None and not isinstance(diagnostics, Mapping):
        raise SchemaValidationError("diagnostics must be an object")


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{field_name} must be an object")
    return value


def _require_fields(record: Mapping[str, object], required: Sequence[str]) -> None:
    missing = [field for field in required if field not in record]
    if missing:
        raise SchemaValidationError(f"missing required fields: {', '.join(missing)}")


def _require_string_fields(
    record: Mapping[str, object],
    fields: Sequence[str],
) -> None:
    for field in fields:
        if not isinstance(record[field], str):
            raise SchemaValidationError(f"{field} must be a string")


def _require_optional_string(value: object, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise SchemaValidationError(f"{field_name} must be a string or null")


def _require_string_sequence(value: object, field_name: str) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{field_name} must be a list of strings")
    if any(not isinstance(item, str) for item in value):
        raise SchemaValidationError(f"{field_name} must be a list of strings")


def _require_edges(value: object, runtime_ids: set[str]) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError("edges must be a list")
    for edge in value:
        edge_record = _require_mapping(edge, "edge")
        _require_fields(edge_record, ("parent_node_id", "node_id"))
        parent_node_id = edge_record["parent_node_id"]
        node_id = edge_record["node_id"]
        if not isinstance(parent_node_id, str) or not isinstance(node_id, str):
            raise SchemaValidationError("edge ids must be strings")
        _reject_runtime_identity_value(
            parent_node_id,
            runtime_ids,
            "edge.parent_node_id",
        )
        _reject_runtime_identity_value(node_id, runtime_ids, "edge.node_id")


def _reject_runtime_identity_keys(record: Mapping[str, object]) -> None:
    present = sorted(set(record) & _PROVENANCE_RUNTIME_IDS)
    if present:
        raise SchemaValidationError(
            f"runtime ids are not material identity fields: {', '.join(present)}"
        )


def _runtime_id_values(provenance: Mapping[str, object]) -> set[str]:
    return {
        value
        for field in _PROVENANCE_RUNTIME_IDS
        if isinstance((value := provenance.get(field)), str) and value
    }


def _reject_runtime_identity_value(
    value: str,
    runtime_ids: set[str],
    field_name: str,
) -> None:
    if value in runtime_ids:
        raise SchemaValidationError(f"runtime id cannot be used as {field_name}")


def _reject_runtime_path_part(path: str, runtime_ids: set[str]) -> None:
    for part in PurePosixPath(path).parts:
        if part in runtime_ids:
            raise SchemaValidationError("runtime id cannot be used in material_path")
