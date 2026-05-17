from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Set

from learnable.core.errors import LearnableError
from learnable.materials.schemas import validate_graph_record


class GraphValidationError(LearnableError, ValueError):
    """Raised when a material graph is not a single valid rooted tree."""


_CANONICAL_METADATA_FIELDS = (
    "node_id",
    "parent_node_id",
    "depth",
    "learnable_session_id",
    "material_path",
)


def validate_graph_integrity(
    graph: Mapping[str, object],
    *,
    material_node_ids: Set[str],
    material_records_by_node: Mapping[str, Mapping[str, object]] | None = None,
    max_depth: int = 20,
) -> None:
    """Validate graph topology and material metadata completeness."""

    _reject_duplicate_node_ids_before_schema(graph)
    validate_graph_record(graph)
    nodes = _nodes(graph)
    root_node_id = _string(graph["root_node_id"], "root_node_id")
    if root_node_id not in nodes:
        raise GraphValidationError("missing root node")

    roots = [
        node_id
        for node_id, node in nodes.items()
        if node.get("parent_node_id") is None
    ]
    if not roots:
        raise GraphValidationError("cycle")
    if len(roots) > 1:
        raise GraphValidationError("multiple roots")
    if roots != [root_node_id]:
        raise GraphValidationError("missing root")

    children: dict[str, list[str]] = defaultdict(list)
    incoming_counts: dict[str, int] = defaultdict(int)
    seen_edges: set[tuple[str, str]] = set()
    for edge in _edges(graph):
        parent = _string(edge["parent_node_id"], "parent_node_id")
        child = _string(edge["node_id"], "node_id")
        edge_key = (parent, child)
        if edge_key in seen_edges:
            raise GraphValidationError("duplicate edge")
        seen_edges.add(edge_key)
        if parent not in nodes:
            raise GraphValidationError("missing parent")
        if child not in nodes:
            raise GraphValidationError("missing child")
        if nodes[child].get("parent_node_id") != parent:
            raise GraphValidationError("missing parent")
        children[parent].append(child)
        incoming_counts[child] += 1

    for node_id, node in nodes.items():
        parent = node.get("parent_node_id")
        if parent is not None and parent not in nodes:
            raise GraphValidationError("missing parent")
        if parent is None and incoming_counts[node_id] != 0:
            raise GraphValidationError("invalid incoming edge count")
        if parent is not None and incoming_counts[node_id] != 1:
            raise GraphValidationError("invalid incoming edge count")
        if parent is not None and not any(
            node_id in values for values in children.values()
        ):
            raise GraphValidationError("missing parent")

    _validate_depths(nodes, children, root_node_id, max_depth)
    graph_node_ids = set(nodes)
    material_ids = set(material_node_ids)
    if graph_node_ids != material_ids:
        raise GraphValidationError("node metadata missing from graph")
    if material_records_by_node is not None:
        _validate_material_metadata(graph, nodes, material_records_by_node)


def _validate_material_metadata(
    graph: Mapping[str, object],
    nodes: Mapping[str, Mapping[str, object]],
    material_records_by_node: Mapping[str, Mapping[str, object]],
) -> None:
    graph_session_id = _string(graph["learnable_session_id"], "learnable_session_id")
    if set(nodes) != set(material_records_by_node):
        raise GraphValidationError(_metadata_missing_message())

    for node_id, graph_node in nodes.items():
        material = material_records_by_node.get(node_id)
        if material is None:
            raise GraphValidationError(_metadata_missing_message())
        if graph_node.get("node_id") != node_id:
            raise GraphValidationError(_metadata_mismatch_message("node_id"))
        if material.get("node_id") != node_id:
            raise GraphValidationError(_metadata_mismatch_message("node_id"))
        if material.get("parent_node_id") != graph_node.get("parent_node_id"):
            raise GraphValidationError(_metadata_mismatch_message("parent_node_id"))
        if material.get("depth") != graph_node.get("depth"):
            raise GraphValidationError(_metadata_mismatch_message("depth"))
        if material.get("learnable_session_id") != graph_session_id:
            raise GraphValidationError(
                _metadata_mismatch_message("learnable_session_id")
            )
        expected_material_path = (
            f"sessions/{graph_session_id}/nodes/{node_id}/material.json"
        )
        if graph_node.get("material_path") != expected_material_path:
            raise GraphValidationError(_metadata_mismatch_message("material_path"))


def _metadata_missing_message() -> str:
    return (
        "metadata missing; canonical metadata fields: "
        f"{', '.join(_CANONICAL_METADATA_FIELDS)}"
    )


def _metadata_mismatch_message(field_name: str) -> str:
    return (
        f"metadata mismatch; canonical metadata field mismatch: {field_name}; "
        f"canonical metadata fields: {', '.join(_CANONICAL_METADATA_FIELDS)}"
    )


def _reject_duplicate_node_ids_before_schema(graph: Mapping[str, object]) -> None:
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, Mapping):
        return
    seen: set[str] = set()
    for value in raw_nodes.values():
        if not isinstance(value, Mapping):
            continue
        node_id = value.get("node_id")
        if not isinstance(node_id, str):
            continue
        if node_id in seen:
            raise GraphValidationError("duplicate node id")
        seen.add(node_id)


def _validate_depths(
    nodes: Mapping[str, Mapping[str, object]],
    children: Mapping[str, list[str]],
    root_node_id: str,
    max_depth: int,
) -> None:
    visited: set[str] = set()
    visiting: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(root_node_id, 0)])
    while queue:
        node_id, expected_depth = queue.popleft()
        if node_id in visiting:
            raise GraphValidationError("cycle")
        visiting.add(node_id)
        node = nodes[node_id]
        depth = node.get("depth")
        if not isinstance(depth, int) or isinstance(depth, bool):
            raise GraphValidationError("invalid depth")
        if depth != expected_depth:
            raise GraphValidationError("invalid depth")
        if depth > max_depth:
            raise GraphValidationError("depth limit")
        visited.add(node_id)
        for child in children.get(node_id, []):
            queue.append((child, expected_depth + 1))
        visiting.remove(node_id)

    if set(nodes) - visited:
        raise GraphValidationError("cycle")


def _nodes(graph: Mapping[str, object]) -> Mapping[str, Mapping[str, object]]:
    raw_nodes = graph["nodes"]
    if not isinstance(raw_nodes, Mapping):
        raise GraphValidationError("nodes must be an object")
    return {
        str(node_id): node
        for node_id, node in raw_nodes.items()
        if isinstance(node, Mapping)
    }


def _edges(graph: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_edges = graph["edges"]
    if not isinstance(raw_edges, list):
        raise GraphValidationError("edges must be a list")
    return [edge for edge in raw_edges if isinstance(edge, Mapping)]


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(f"{field_name} must be a string")
    return value
