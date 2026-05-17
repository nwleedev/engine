from __future__ import annotations

import pytest

from learnable.materials.schemas import (
    SchemaValidationError,
    validate_graph_record,
    validate_provenance,
)


def test_validate_provenance_accepts_only_documented_optional_fields() -> None:
    validate_provenance(
        {
            "runtime": "claude",
            "codex_thread_id": "runtime-thread-a",
            "codex_session_id": "runtime-session-a",
            "codex_turn_id": "runtime-turn-a",
            "app_server_thread_id": "app-thread-a",
            "diagnostics": {"source": "unit-test"},
        }
    )

    with pytest.raises(SchemaValidationError, match="extra"):
        validate_provenance({"runtime": "codex", "extra": "not-allowed"})


@pytest.mark.parametrize("runtime", ["codex", "claude", "unknown"])
def test_validate_provenance_accepts_documented_runtime_values(runtime: str) -> None:
    validate_provenance({"runtime": runtime})


def test_validate_provenance_rejects_unknown_runtime_values() -> None:
    with pytest.raises(SchemaValidationError, match="runtime"):
        validate_provenance({"runtime": "local-shell"})


def test_mismatched_runtime_ids_are_valid_metadata_not_graph_identity() -> None:
    validate_graph_record(
        {
            "schema_version": "1.0",
            "learnable_session_id": "learnable-session-001",
            "root_node_id": "node-root",
            "nodes": {
                "node-root": {
                    "node_id": "node-root",
                    "parent_node_id": None,
                    "depth": 0,
                    "material_path": "learnable-session-001/node-root/material.json",
                },
                "node-child": {
                    "node_id": "node-child",
                    "parent_node_id": "node-root",
                    "depth": 1,
                    "material_path": "learnable-session-001/node-child/material.json",
                },
            },
            "edges": [{"parent_node_id": "node-root", "node_id": "node-child"}],
            "created_at": "2026-05-18T09:00:00Z",
            "updated_at": "2026-05-18T09:30:00Z",
            "provenance": {
                "runtime": "codex",
                "codex_thread_id": "runtime-thread-other",
                "codex_session_id": "runtime-session-other",
            },
        }
    )
