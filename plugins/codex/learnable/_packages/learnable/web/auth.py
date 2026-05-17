from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

from learnable.materials.events import append_audit


class AuthResult(Enum):
    """Token authentication outcomes that never include the token value."""

    OK = "ok"
    MISSING = "missing"
    INVALID = "invalid"


@dataclass(frozen=True)
class BoundaryResult:
    """Host and origin validation result for local-only requests."""

    ok: bool
    status: int
    error: str | None = None


_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def verify_token(
    project_root: Path,
    headers: dict[str, str],
    *,
    audit_path: Path | None = None,
    action: str | None = None,
) -> AuthResult:
    expected = _token_path(project_root).read_text(encoding="utf-8").strip()
    actual = _extract_token(headers)
    if actual is None:
        result = AuthResult.MISSING
    elif actual == expected:
        result = AuthResult.OK
    else:
        result = AuthResult.INVALID
    if action is not None and audit_path is not None and result is not AuthResult.OK:
        append_audit(
            audit_path,
            request={"auth": result.value},
            action={"name": action, "status": "denied"},
        )
    return result


def verify_loopback_request(client_host: str, headers: dict[str, str]) -> BoundaryResult:
    host_header = headers.get("host", client_host)
    host = _split_host(host_header)
    if _normalize_host(client_host) not in _LOOPBACK_HOSTS:
        return BoundaryResult(False, 403, "client_not_loopback")
    if host not in _LOOPBACK_HOSTS:
        return BoundaryResult(False, 403, "host_not_loopback")
    origin = headers.get("origin")
    if origin:
        parsed = urlparse(origin)
        origin_host = _normalize_host(parsed.hostname or "")
        if origin_host not in _LOOPBACK_HOSTS:
            return BoundaryResult(False, 403, "origin_not_loopback")
    return BoundaryResult(True, 200)


def _extract_token(headers: dict[str, str]) -> str | None:
    authorization = headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    token = headers.get("x-learnable-token")
    if token:
        return token.strip()
    return None


def _split_host(value: str) -> str:
    if value.startswith("["):
        end = value.find("]")
        return _normalize_host(value[1:end] if end > 0 else value)
    return _normalize_host(value.rsplit(":", 1)[0] if ":" in value else value)


def _normalize_host(value: str) -> str:
    return value.strip().lower()


def _token_path(project_root: Path) -> Path:
    return project_root / ".codex" / "materials" / ".server" / "token"
