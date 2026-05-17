from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from learnable.cli import main
from learnable.materials.events import read_audits
from learnable.materials.file_store import FileMaterialStore
from learnable.server import select_backend
from learnable.web.static import StaticResourceError, read_static_resource
from learnable.web.stdlib_backend import create_server


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _request(
    url: str,
    *,
    method: str = "GET",
    token: str | None = None,
) -> urllib.response.addinfourl:
    headers = {"Host": "127.0.0.1"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method=method)
    return urllib.request.urlopen(request, timeout=5)


def test_threading_http_server_serves_spa_api_and_shutdown(tmp_path: Path) -> None:
    store = FileMaterialStore(tmp_path)
    session = store.create_session(
        title="Root",
        prompt="Explain",
        markdown="# Root\n",
        provenance={"runtime": "codex"},
    )
    token_path = tmp_path / ".codex" / "materials" / ".server" / "token"
    token = token_path.read_text(encoding="utf-8").strip()
    port = _free_port()
    httpd = create_server(
        project_root=tmp_path,
        host="127.0.0.1",
        port=port,
        requested_backend="stdlib",
        selected_backend="stdlib",
        backend_preflight={"requested": "stdlib", "selected": "stdlib"},
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        index = _request(f"http://127.0.0.1:{port}/").read().decode("utf-8")
        status = json.loads(
            _request(f"http://127.0.0.1:{port}/api/status").read().decode("utf-8")
        )
        tree = json.loads(
            _request(
                (
                    f"http://127.0.0.1:{port}/api/materials/tree"
                    f"?learnable_session_id={session['learnable_session_id']}"
                )
            )
            .read()
            .decode("utf-8")
        )

        assert "<!doctype html>" in index.lower()
        assert status["selected_backend"] == "stdlib"
        assert tree["tree"]["root_node_id"] == session["root_node_id"]
        with pytest.raises(urllib.error.HTTPError) as denied:
            _request(f"http://127.0.0.1:{port}/api/server/shutdown", method="POST")
        assert denied.value.code == 401
        _request(
            f"http://127.0.0.1:{port}/api/server/shutdown",
            method="POST",
            token=token,
        ).read()
        thread.join(timeout=5)
    finally:
        httpd.server_close()

    audits = read_audits(tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl")
    assert audits[-1]["action"]["name"] == "shutdown"
    assert audits[-1]["action"]["status"] == "accepted"


def test_create_server_reports_port_conflict(tmp_path: Path) -> None:
    port = _free_port()
    first = create_server(
        project_root=tmp_path,
        host="127.0.0.1",
        port=port,
        requested_backend="stdlib",
        selected_backend="stdlib",
        backend_preflight={},
    )
    try:
        with pytest.raises(OSError, match="port unavailable"):
            create_server(
                project_root=tmp_path,
                host="127.0.0.1",
                port=port,
                requested_backend="stdlib",
                selected_backend="stdlib",
                backend_preflight={},
            )
    finally:
        first.server_close()


def test_create_server_rejects_non_loopback_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="host must be loopback"):
        create_server(
            project_root=tmp_path,
            host="0.0.0.0",
            port=0,
            requested_backend="stdlib",
            selected_backend="stdlib",
            backend_preflight={},
        )


def test_create_server_does_not_initialize_missing_storage(tmp_path: Path) -> None:
    httpd = create_server(
        project_root=tmp_path,
        host="127.0.0.1",
        port=0,
        requested_backend="stdlib",
        selected_backend="stdlib",
        backend_preflight={},
    )
    try:
        assert not (tmp_path / ".codex" / "materials").exists()
    finally:
        httpd.server_close()


def test_auto_backend_falls_back_to_stdlib_when_asgi_preflight_fails() -> None:
    selection = select_backend("auto")

    assert selection.requested == "auto"
    assert selection.selected == "stdlib"
    assert selection.preflight["asgi"]["available"] is False


def test_static_resource_lookup_failure_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    from learnable.web import static

    class MissingFiles:
        def joinpath(self, *parts: str) -> "MissingFiles":
            return self

        def is_file(self) -> bool:
            return False

    monkeypatch.setattr(static.resources, "files", lambda package: MissingFiles())

    with pytest.raises(StaticResourceError, match="static resource not found"):
        read_static_resource("index.html")


def test_cli_serve_reports_requested_and_selected_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_server(**kwargs: object) -> None:
        assert kwargs["requested_backend"] == "auto"
        assert kwargs["selected_backend"] == "stdlib"

    monkeypatch.setattr("learnable.cli.run_server", fake_run_server)

    result = main(
        [
            "--project-root",
            str(tmp_path),
            "serve",
            "--backend",
            "auto",
            "--port",
            "0",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "requested_backend=auto" in output
    assert "selected_backend=stdlib" in output
    assert str(tmp_path) not in output


def test_cli_stop_calls_local_shutdown_endpoint_with_token_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = FileMaterialStore(tmp_path)
    store.init()
    token_file = tmp_path / ".codex" / "materials" / ".server" / "token"
    calls: list[tuple[str, str]] = []

    def fake_shutdown(url: str, token: str) -> None:
        calls.append((url, token))

    monkeypatch.setattr("learnable.cli.request_shutdown", fake_shutdown)

    result = main(
        [
            "--project-root",
            str(tmp_path),
            "stop",
            "--token-file",
            ".codex/materials/.server/token",
            "--port",
            "8123",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert calls == [
        (
            "http://127.0.0.1:8123/api/server/shutdown",
            token_file.read_text(encoding="utf-8").strip(),
        )
    ]
    assert "shutdown requested" in output
    assert str(tmp_path) not in output
