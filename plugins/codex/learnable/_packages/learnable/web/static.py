from __future__ import annotations

from importlib import resources
from pathlib import PurePosixPath


class StaticResourceError(LookupError):
    """Raised when a bundled static resource cannot be read safely."""


_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def read_static_resource(path: str) -> tuple[bytes, str]:
    """Read a static package resource without allowing path traversal."""

    normalized = PurePosixPath(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise StaticResourceError("static resource not found")
    resource = resources.files("learnable").joinpath("static", *normalized.parts)
    if not resource.is_file():
        raise StaticResourceError("static resource not found")
    suffix = normalized.suffix
    return resource.read_bytes(), _CONTENT_TYPES.get(suffix, "application/octet-stream")
