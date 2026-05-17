from __future__ import annotations

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from learnable.materials.file_store import FileMaterialStore
from learnable.web.handlers import HandlerContext, Response, handle_request


class LearnableHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer carrying Learnable handler dependencies."""

    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        context: HandlerContext,
    ) -> None:
        self.learnable_context = context
        super().__init__(server_address, handler_class)


class LearnableRequestHandler(BaseHTTPRequestHandler):
    """Adapter from stdlib HTTP requests to Learnable router responses."""

    server: LearnableHTTPServer

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle(self) -> None:
        headers = {key.lower(): value for key, value in self.headers.items()}
        response = handle_request(
            self.server.learnable_context,
            self.command,
            self.path,
            headers,
            str(self.client_address[0]),
        )
        self._send(response)

    def _send(self, response: Response) -> None:
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        for key, value in (response.headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response.body)


def create_server(
    *,
    project_root: Path,
    host: str,
    port: int,
    requested_backend: str,
    selected_backend: str,
    backend_preflight: dict[str, object],
) -> LearnableHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("host must be loopback")
    store = FileMaterialStore(project_root)

    context = HandlerContext(
        project_root=project_root,
        store=store,
        requested_backend=requested_backend,
        selected_backend=selected_backend,
        backend_preflight=backend_preflight,
    )
    try:
        server = LearnableHTTPServer((host, port), LearnableRequestHandler, context)
    except OSError as exc:
        raise OSError("port unavailable") from exc

    def shutdown_later() -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    context.shutdown_callback = shutdown_later
    return server


def run_stdlib_server(
    *,
    project_root: Path,
    host: str,
    port: int,
    requested_backend: str,
    selected_backend: str,
    backend_preflight: dict[str, object],
) -> None:
    server = create_server(
        project_root=project_root,
        host=host,
        port=port,
        requested_backend=requested_backend,
        selected_backend=selected_backend,
        backend_preflight=backend_preflight,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
