from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from learnable.core.config import default_server_config, read_server_config
from learnable.core.redaction import redact_text
from learnable.materials.events import append_audit
from learnable.materials.file_store import FileMaterialStore
from learnable.materials.schemas import SchemaValidationError
from learnable.web.auth import AuthResult, verify_loopback_request, verify_token
from learnable.web.router import RouteNotFound, Router
from learnable.web.static import StaticResourceError, read_static_resource

_SENSITIVE_RESPONSE_KEYS = frozenset(
    {"authorization", "api_key", "apikey", "key", "password", "secret", "token"}
)
_PATH_RESPONSE_KEYS = frozenset(
    {"path", "root", "project_root", "projectroot", "materials_root", "materialsroot"}
)


@dataclass(frozen=True)
class Response:
    """Serialized HTTP response returned by router handlers."""

    status: int
    body: bytes
    content_type: str = "application/json; charset=utf-8"
    headers: dict[str, str] | None = None


@dataclass(frozen=True)
class Request:
    """Normalized request data independent of BaseHTTPRequestHandler."""

    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    client_host: str


@dataclass
class HandlerContext:
    """Dependencies needed by read-only Learnable HTTP handlers."""

    project_root: Path
    store: FileMaterialStore
    requested_backend: str
    selected_backend: str
    backend_preflight: dict[str, object]
    shutdown_callback: Callable[[], None] | None = None


def handle_request(
    context: HandlerContext,
    method: str,
    target: str,
    headers: Mapping[str, str],
    client_host: str,
) -> Response:
    parsed = urlparse(target)
    request = Request(
        method=method.upper(),
        path=parsed.path or "/",
        query=parse_qs(parsed.query, keep_blank_values=True),
        headers={str(key).lower(): str(value) for key, value in headers.items()},
        client_host=client_host,
    )
    boundary = verify_loopback_request(client_host, request.headers)
    if not boundary.ok:
        return _json({"error": boundary.error}, boundary.status)
    try:
        return _router().resolve(request.method, request.path)(context, request)
    except RouteNotFound:
        return _json({"error": "not_found"}, 404)
    except SchemaValidationError:
        return _json({"error": "material_schema_invalid"}, 500)
    except (OSError, ValueError, KeyError, TypeError, StaticResourceError) as exc:
        return _json({"error": "request_failed", "detail": redact_text(type(exc).__name__)}, 500)


def _router() -> Router:
    router = Router()
    router.add("GET", "/", _index)
    router.add("GET", "/assets/", _asset, prefix=True)
    router.add("GET", "/api/status", _status)
    router.add("GET", "/api/sessions", _sessions)
    router.add("GET", "/api/materials/tree", _tree)
    router.add("GET", "/api/materials/node", _node)
    router.add("POST", "/api/server/reload", _reload)
    router.add("POST", "/api/server/shutdown", _shutdown)
    return router


def _index(context: HandlerContext, request: Request) -> Response:
    return _static("index.html")


def _asset(context: HandlerContext, request: Request) -> Response:
    return _static(request.path.removeprefix("/assets/"))


def _status(context: HandlerContext, request: Request) -> Response:
    return _json(
        {
            "project_root": ".",
            "materials_root": ".codex/materials",
            "schema_version": _schema_version(context),
            "requested_backend": context.requested_backend,
            "selected_backend": context.selected_backend,
            "backend_preflight": context.backend_preflight,
            "server_config": _safe_server_config(context.project_root),
        },
        200,
    )


def _sessions(context: HandlerContext, request: Request) -> Response:
    return _json({"sessions": _sessions_from_index(context.project_root)}, 200)


def _tree(context: HandlerContext, request: Request) -> Response:
    session_id = _required_query(request, "learnable_session_id")
    tree = context.store.load_tree(session_id)
    return _json({"tree": tree, "children_by_parent": _children_by_parent(tree)}, 200)


def _node(context: HandlerContext, request: Request) -> Response:
    session_id = _required_query(request, "learnable_session_id")
    node_id = _required_query(request, "node_id")
    material, markdown = context.store.load_node(session_id, node_id)
    tree = context.store.load_tree(session_id)
    node_meta = _node_meta(tree, node_id)
    safe_material = _safe_material(material)
    return _json(
        {
            "material": safe_material,
            "node_metadata": node_meta,
            "markdown": markdown,
            "parent_node_id": safe_material["parent_node_id"],
            "child_node_ids": _children_by_parent(tree).get(node_id, []),
            "source_refs": safe_material["source_refs"],
            "runtime_provenance": safe_material.get("provenance", {}),
        },
        200,
    )


def _reload(context: HandlerContext, request: Request) -> Response:
    auth = _require_token(context, request, "reload")
    if auth is not None:
        return auth
    context.store.init()
    _audit(context, request, "reload", "accepted")
    return _json({"ok": True, "action": "reload"}, 200)


def _shutdown(context: HandlerContext, request: Request) -> Response:
    auth = _require_token(context, request, "shutdown")
    if auth is not None:
        return auth
    _audit(context, request, "shutdown", "accepted")
    if context.shutdown_callback is not None:
        context.shutdown_callback()
    return _json({"ok": True, "action": "shutdown"}, 200)


def _require_token(
    context: HandlerContext,
    request: Request,
    action: str,
) -> Response | None:
    result = verify_token(
        context.project_root,
        request.headers,
        audit_path=_audit_path(context.project_root),
        action=action,
    )
    if result is AuthResult.OK:
        return None
    status = 401 if result is AuthResult.MISSING else 403
    return _json({"error": f"auth_{result.value}"}, status)


def _audit(
    context: HandlerContext,
    request: Request,
    action: str,
    status: str,
) -> None:
    append_audit(
        _audit_path(context.project_root),
        request={"method": request.method, "path": request.path},
        action={"name": action, "status": status},
    )


def _static(path: str) -> Response:
    body, content_type = read_static_resource(path)
    return Response(200, body, content_type)


def _json(payload: Mapping[str, object], status: int) -> Response:
    return Response(
        status=status,
        body=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )


def _required_query(request: Request, name: str) -> str:
    values = request.query.get(name)
    if not values or not values[0]:
        raise ValueError(f"missing query parameter {name}")
    return values[0]


def _schema_version(context: HandlerContext) -> str:
    index_path = context.project_root / ".codex" / "materials" / "index.json"
    if not index_path.exists():
        return "missing"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return str(data.get("schema_version", "unknown"))


def _sessions_from_index(project_root: Path) -> list[dict[str, object]]:
    index_path = project_root / ".codex" / "materials" / "index.json"
    if not index_path.exists():
        return []
    data = json.loads(index_path.read_text(encoding="utf-8"))
    sessions = data.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("material index sessions must be a list")
    return [dict(item) for item in sessions if isinstance(item, Mapping)]


def _safe_material(material: Mapping[str, object]) -> dict[str, object]:
    safe = dict(material)
    provenance = safe.get("provenance")
    if isinstance(provenance, Mapping):
        safe["provenance"] = _safe_provenance(provenance)
    return safe


def _safe_provenance(provenance: Mapping[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in provenance.items():
        key_text = str(key)
        if isinstance(value, str):
            safe[key_text] = _safe_response_value(key_text, value)
        elif isinstance(value, Mapping):
            safe[key_text] = {
                str(child_key): _safe_response_value(str(child_key), str(child_value))
                for child_key, child_value in value.items()
            }
        else:
            safe[key_text] = value
    return safe


def _safe_response_value(key: str, value: str) -> str:
    lowered = key.lower()
    if lowered in _SENSITIVE_RESPONSE_KEYS:
        return "[REDACTED:secret]"
    if lowered in _PATH_RESPONSE_KEYS or lowered.endswith("_path") or lowered.endswith("_root"):
        return "[REDACTED:path]"
    return redact_text(value)


def _safe_server_config(project_root: Path) -> dict[str, object]:
    try:
        config = read_server_config(project_root)
        stale = config != default_server_config(project_root)
    except Exception:
        return {"present": False, "stale": True}
    return {
        "present": True,
        "stale": stale,
        "projectRoot": ".",
        "materialsRoot": ".codex/materials",
        "serverStateRoot": ".codex/materials/.server",
        "configPath": ".codex/materials/.server/config.json",
        "auditLogPath": ".codex/materials/.server/audits.jsonl",
    }


def _children_by_parent(tree: Mapping[str, object]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    edges = tree.get("edges", [])
    if not isinstance(edges, list):
        return children
    for edge in edges:
        if not isinstance(edge, Mapping):
            continue
        parent = edge.get("parent_node_id")
        child = edge.get("node_id")
        if isinstance(parent, str) and isinstance(child, str):
            children.setdefault(parent, []).append(child)
    return children


def _node_meta(tree: Mapping[str, object], node_id: str) -> object:
    nodes = tree.get("nodes")
    if isinstance(nodes, Mapping):
        return nodes.get(node_id, {})
    return {}


def _audit_path(project_root: Path) -> Path:
    return project_root / ".codex" / "materials" / ".server" / "audits.jsonl"
