from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnable.materials.file_store import FileMaterialStore
from learnable.web.handlers import HandlerContext, handle_request
from learnable.web.router import RouteNotFound, Router


def _context(project_root: Path) -> HandlerContext:
    store = FileMaterialStore(project_root)
    store.init()
    return HandlerContext(
        project_root=project_root,
        store=store,
        requested_backend="auto",
        selected_backend="stdlib",
        backend_preflight={
            "requested": "auto",
            "selected": "stdlib",
            "asgi": {"available": False, "reason": "not installed"},
        },
    )


def _json(response_body: bytes) -> dict[str, object]:
    parsed = json.loads(response_body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return parsed


def _create_tree(project_root: Path) -> tuple[str, str, str]:
    store = FileMaterialStore(project_root)
    session = store.create_session(
        title="Root",
        prompt="Explain",
        markdown="# Root\n",
        provenance={"runtime": "codex", "codex_session_id": "runtime-session"},
        source_refs=[{"source_id": "source-001"}],
    )
    child = store.add_child(
        learnable_session_id=str(session["learnable_session_id"]),
        parent_node_id=str(session["root_node_id"]),
        title="Child",
        prompt="More",
        markdown="## Child\n",
        provenance={"runtime": "codex"},
        source_refs=["source-002"],
    )
    return (
        str(session["learnable_session_id"]),
        str(session["root_node_id"]),
        str(child["node_id"]),
    )


def _snapshot_materials(project_root: Path) -> dict[str, str]:
    root = project_root / ".codex" / "materials"
    return {
        str(item.relative_to(project_root)): item.read_text(encoding="utf-8")
        for item in sorted(root.rglob("*"))
        if item.is_file()
    }


def test_router_dispatches_exact_and_prefixed_paths() -> None:
    router = Router()
    router.add("GET", "/api/status", lambda request: "status")
    router.add("GET", "/assets/", lambda request: "asset", prefix=True)

    assert router.resolve("GET", "/api/status")(object()) == "status"
    assert router.resolve("GET", "/assets/app.css")(object()) == "asset"
    with pytest.raises(RouteNotFound):
        router.resolve("POST", "/api/status")


def test_status_response_exposes_backend_and_redacted_config(tmp_path: Path) -> None:
    context = _context(tmp_path)

    response = handle_request(context, "GET", "/api/status", {}, "127.0.0.1")

    payload = _json(response.body)
    serialized = json.dumps(payload, sort_keys=True)
    assert response.status == 200
    assert payload["project_root"] == "."
    assert payload["materials_root"] == ".codex/materials"
    assert payload["schema_version"] == "1.0"
    assert payload["requested_backend"] == "auto"
    assert payload["selected_backend"] == "stdlib"
    assert "token" not in serialized.lower()
    assert str(tmp_path) not in serialized


def test_status_and_sessions_do_not_create_missing_storage(tmp_path: Path) -> None:
    context = HandlerContext(
        project_root=tmp_path,
        store=FileMaterialStore(tmp_path),
        requested_backend="auto",
        selected_backend="stdlib",
        backend_preflight={},
    )

    status = _json(handle_request(context, "GET", "/api/status", {}, "127.0.0.1").body)
    sessions = _json(handle_request(context, "GET", "/api/sessions", {}, "127.0.0.1").body)

    assert status["schema_version"] == "missing"
    assert sessions["sessions"] == []
    assert not (tmp_path / ".codex" / "materials").exists()


def test_status_marks_stale_server_config_without_leaking_paths(tmp_path: Path) -> None:
    context = _context(tmp_path)
    config_path = tmp_path / ".codex" / "materials" / ".server" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["tokenPath"] = "/outside/token"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    response = handle_request(context, "GET", "/api/status", {}, "127.0.0.1")

    payload = _json(response.body)
    serialized = json.dumps(payload, sort_keys=True)
    assert response.status == 200
    assert payload["server_config"]["stale"] is True
    assert "/outside/token" not in serialized
    assert str(tmp_path) not in serialized


def test_material_read_apis_expose_tree_node_relationships_and_markdown(
    tmp_path: Path,
) -> None:
    session_id, root_node_id, child_node_id = _create_tree(tmp_path)
    context = _context(tmp_path)

    sessions = _json(handle_request(context, "GET", "/api/sessions", {}, "127.0.0.1").body)
    tree = _json(
        handle_request(
            context,
            "GET",
            f"/api/materials/tree?learnable_session_id={session_id}",
            {},
            "127.0.0.1",
        ).body
    )
    node = _json(
        handle_request(
            context,
            "GET",
            f"/api/materials/node?learnable_session_id={session_id}&node_id={child_node_id}",
            {},
            "127.0.0.1",
        ).body
    )

    assert sessions["sessions"][0]["learnable_session_id"] == session_id
    assert tree["tree"]["root_node_id"] == root_node_id
    assert tree["children_by_parent"][root_node_id] == [child_node_id]
    assert node["material"]["node_id"] == child_node_id
    assert node["material"]["parent_node_id"] == root_node_id
    assert node["markdown"] == "## Child\n"
    assert node["source_refs"] == ["source-002"]
    assert node["runtime_provenance"] == {"runtime": "codex"}


def test_node_api_redacts_sensitive_provenance_diagnostics(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Root",
        prompt="Explain",
        markdown="# Root\n",
        provenance={
            "runtime": "codex",
            "diagnostics": {
                "project_root": str(tmp_path),
                "token": "learnable-token-12345",
            },
        },
    )
    context = _context(tmp_path)

    response = handle_request(
        context,
        "GET",
        (
            "/api/materials/node"
            f"?learnable_session_id={session['learnable_session_id']}"
            f"&node_id={session['root_node_id']}"
        ),
        {},
        "127.0.0.1",
    )

    payload = _json(response.body)
    serialized = json.dumps(payload, sort_keys=True)
    assert response.status == 200
    assert str(tmp_path) not in serialized
    assert "learnable-token-12345" not in serialized
    assert "[REDACTED:path]" in serialized
    assert "[REDACTED:secret]" in serialized


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/materials/generate"),
        ("POST", "/api/ask"),
        ("POST", "/api/explain"),
        ("GET", "/api/jobs/job-001"),
        ("GET", "/api/events?learnable_session_id=learnable-session-001&since=0"),
    ],
)
def test_mvp_does_not_expose_browser_originated_generation_apis(
    tmp_path: Path,
    method: str,
    path: str,
) -> None:
    context = _context(tmp_path)
    before = _snapshot_materials(tmp_path)

    response = handle_request(context, method, path, {}, "127.0.0.1")

    assert response.status == 404
    after = _snapshot_materials(tmp_path)
    assert after == before


def test_malformed_material_schema_is_returned_as_safe_error(tmp_path: Path) -> None:
    session_id, root_node_id, _child_node_id = _create_tree(tmp_path)
    material_path = (
        tmp_path
        / ".codex"
        / "materials"
        / "sessions"
        / session_id
        / "nodes"
        / root_node_id
        / "material.json"
    )
    material = json.loads(material_path.read_text(encoding="utf-8"))
    material.pop("source_refs")
    material_path.write_text(json.dumps(material), encoding="utf-8")
    context = _context(tmp_path)

    response = handle_request(
        context,
        "GET",
        f"/api/materials/node?learnable_session_id={session_id}&node_id={root_node_id}",
        {},
        "127.0.0.1",
    )

    payload = _json(response.body)
    assert response.status == 500
    assert payload["error"] == "material_schema_invalid"
    assert str(tmp_path) not in json.dumps(payload)


def test_reload_requires_token_and_appends_redacted_audit(tmp_path: Path) -> None:
    context = _context(tmp_path)
    token = (
        tmp_path / ".codex" / "materials" / ".server" / "token"
    ).read_text(encoding="utf-8").strip()

    denied = handle_request(
        context,
        "POST",
        "/api/server/reload",
        {"authorization": "Bearer learnable-token-12345"},
        "127.0.0.1",
    )
    accepted = handle_request(
        context,
        "POST",
        "/api/server/reload",
        {"authorization": f"Bearer {token}"},
        "127.0.0.1",
    )

    audits_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"
    audits = audits_path.read_text(encoding="utf-8")
    assert denied.status == 403
    assert accepted.status == 200
    assert "learnable-token-12345" not in audits
    assert token not in audits
    assert '"name":"reload"' in audits
    assert '"status":"accepted"' in audits
