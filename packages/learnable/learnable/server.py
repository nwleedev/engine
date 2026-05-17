from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from learnable.web.asgi_backend import preflight as asgi_preflight
from learnable.web.stdlib_backend import run_stdlib_server


@dataclass(frozen=True)
class BackendSelection:
    """Selected Learnable HTTP backend and diagnostic preflight data."""

    requested: str
    selected: str
    preflight: dict[str, object]


def select_backend(requested: str) -> BackendSelection:
    """Select the local server backend without requiring optional frameworks."""

    if requested not in {"auto", "stdlib", "asgi"}:
        raise ValueError("backend must be auto, stdlib, or asgi")
    asgi = asgi_preflight()
    if requested == "stdlib":
        selected = "stdlib"
    elif requested == "asgi":
        if not asgi["available"]:
            raise RuntimeError("asgi backend unavailable")
        selected = "asgi"
    else:
        selected = "asgi" if asgi["available"] else "stdlib"
    return BackendSelection(
        requested=requested,
        selected=selected,
        preflight={
            "requested": requested,
            "selected": selected,
            "asgi": asgi,
        },
    )


def run_server(
    *,
    project_root: Path,
    host: str,
    port: int,
    requested_backend: str,
    selected_backend: str,
    backend_preflight: dict[str, object],
) -> None:
    """Run the selected Learnable local server until interrupted or shut down."""

    if selected_backend != "stdlib":
        raise RuntimeError("only stdlib backend is available in the MVP")
    run_stdlib_server(
        project_root=project_root,
        host=host,
        port=port,
        requested_backend=requested_backend,
        selected_backend=selected_backend,
        backend_preflight=backend_preflight,
    )
