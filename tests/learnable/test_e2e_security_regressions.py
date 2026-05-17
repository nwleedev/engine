from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from learnable.cli import main
from learnable.materials.events import read_audits
from learnable.web.stdlib_backend import create_server


SCN_E2E_READ_PATH = "SCN-LRN-011-001"
SCN_FORBIDDEN_GENERATION_ROUTES = "SCN-LRN-011-002"
SCN_BROWSER_AUTH_BOOTSTRAP_ABSENT = "SCN-LRN-011-003"


def _run(project_root: Path, *args: str) -> int:
    return main(["--project-root", str(project_root), *args])


def _request(
    port: int,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
) -> tuple[int, bytes]:
    headers = {"Host": "127.0.0.1"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _response(
    port: int,
    path: str,
    *,
    method: str = "GET",
) -> urllib.response.addinfourl:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"Host": "127.0.0.1"},
        method=method,
    )
    return urllib.request.urlopen(request, timeout=5)


def _json(port: int, path: str, *, method: str = "GET") -> dict[str, Any]:
    status, body = _request(port, path, method=method)
    assert status == 200
    payload = json.loads(body.decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def _create_cli_material_graph(project_root: Path) -> tuple[str, str, str]:
    root_markdown = project_root / "root.md"
    child_markdown = project_root / "child.md"
    root_markdown.write_text("# Root\n\nRoot body without secrets.\n", encoding="utf-8")
    child_markdown.write_text("## Child\n\nChild body.\n", encoding="utf-8")

    assert _run(project_root, "init") == 0
    assert (
        _run(
            project_root,
            "ask",
            "--title",
            "Root",
            "--prompt",
            "Explain TOKEN=learnable-token-12345",
            "--markdown-file",
            str(root_markdown),
        )
        == 0
    )
    session = json.loads(
        next((project_root / ".codex" / "materials" / "sessions").iterdir())
        .joinpath("session.json")
        .read_text(encoding="utf-8")
    )
    assert (
        _run(
            project_root,
            "explain",
            "--session",
            str(session["learnable_session_id"]),
            "--parent",
            str(session["root_node_id"]),
            "--title",
            "Child",
            "--prompt",
            "More",
            "--markdown-file",
            str(child_markdown),
        )
        == 0
    )
    graph = json.loads(
        (
            project_root
            / ".codex"
            / "materials"
            / "sessions"
            / str(session["learnable_session_id"])
            / "graph.json"
        ).read_text(encoding="utf-8")
    )
    child_ids = sorted(set(graph["nodes"]) - {str(session["root_node_id"])})
    assert len(child_ids) == 1
    return str(session["learnable_session_id"]), str(session["root_node_id"]), child_ids[0]


@contextmanager
def _running_server(project_root: Path) -> Iterator[int]:
    httpd = create_server(
        project_root=project_root,
        host="127.0.0.1",
        port=0,
        requested_backend="auto",
        selected_backend="stdlib",
        backend_preflight={"requested": "auto", "selected": "stdlib"},
    )
    port = int(httpd.server_address[1])
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


def test_cli_created_material_graph_is_readable_through_http_api(tmp_path: Path) -> None:
    """SCN-LRN-011-001: CLI-created root/child materials are readable over HTTP."""

    assert SCN_E2E_READ_PATH
    session_id, root_node_id, child_node_id = _create_cli_material_graph(tmp_path)

    with _running_server(tmp_path) as port:
        sessions = _json(port, "/api/sessions")
        tree = _json(port, f"/api/materials/tree?learnable_session_id={session_id}")
        node = _json(
            port,
            f"/api/materials/node?learnable_session_id={session_id}&node_id={child_node_id}",
        )

    assert sessions["sessions"][0]["learnable_session_id"] == session_id
    assert tree["tree"]["root_node_id"] == root_node_id
    assert tree["children_by_parent"][root_node_id] == [child_node_id]
    assert node["material"]["parent_node_id"] == root_node_id
    assert node["markdown"] == "## Child\n\nChild body.\n"
    assert not (tmp_path / ".codex" / "session-memory").exists()


def test_http_mutation_non_goals_and_auth_failures_do_not_leak_token(
    tmp_path: Path,
) -> None:
    """SCN-LRN-011-002: browser generation routes are absent and auth errors redact."""

    assert SCN_FORBIDDEN_GENERATION_ROUTES
    _create_cli_material_graph(tmp_path)
    token = (
        tmp_path / ".codex" / "materials" / ".server" / "token"
    ).read_text(encoding="utf-8").strip()

    with _running_server(tmp_path) as port:
        for path in ["/api/ask", "/api/explain", "/api/jobs", "/events"]:
            status, body = _request(port, path, method="POST")
            assert status == 404
            assert token.encode("utf-8") not in body
        status, body = _request(port, "/api/server/shutdown", method="POST")

    audits = read_audits(tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl")
    serialized_audits = json.dumps(audits, sort_keys=True)
    assert status == 401
    assert token not in body.decode("utf-8")
    assert token not in serialized_audits
    assert audits[-1]["action"]["name"] == "shutdown"
    assert audits[-1]["action"]["status"] == "denied"
    assert not (tmp_path / ".codex" / "session-memory").exists()


def test_browser_read_surfaces_do_not_bootstrap_auth_tokens(tmp_path: Path) -> None:
    """SCN-LRN-011-003: browser read surfaces do not issue auth cookies or token URLs."""

    assert SCN_BROWSER_AUTH_BOOTSTRAP_ABSENT
    _create_cli_material_graph(tmp_path)
    with _running_server(tmp_path) as port:
        with _response(port, "/") as index:
            headers = {key.lower(): value for key, value in index.headers.items()}
            body = index.read().decode("utf-8").lower()
        with _response(port, "/api/status") as status:
            status_headers = {key.lower(): value for key, value in status.headers.items()}
            status_body = status.read().decode("utf-8").lower()

    assert "set-cookie" not in headers
    assert "set-cookie" not in status_headers
    assert "location" not in headers
    assert "location" not in status_headers
    assert "token=" not in body
    assert "authorization" not in body
    assert "cookie" not in body
    assert "token=" not in status_body
