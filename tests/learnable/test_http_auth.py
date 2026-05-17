from __future__ import annotations

import json
from pathlib import Path

from learnable.materials.events import read_audits
from learnable.materials.file_store import FileMaterialStore
from learnable.web.auth import AuthResult, verify_loopback_request, verify_token


def test_verify_token_accepts_bearer_or_header_token(tmp_path: Path) -> None:
    FileMaterialStore(tmp_path).init()
    token = (
        tmp_path / ".codex" / "materials" / ".server" / "token"
    ).read_text(encoding="utf-8").strip()

    assert verify_token(tmp_path, {"authorization": f"Bearer {token}"}) == AuthResult.OK
    assert verify_token(tmp_path, {"x-learnable-token": token}) == AuthResult.OK


def test_verify_token_rejects_missing_or_wrong_token_without_leaking_value(
    tmp_path: Path,
) -> None:
    FileMaterialStore(tmp_path).init()

    missing = verify_token(tmp_path, {})
    wrong = verify_token(tmp_path, {"authorization": "Bearer secret-token-value"})

    assert missing == AuthResult.MISSING
    assert wrong == AuthResult.INVALID
    assert "secret-token-value" not in wrong.value


def test_loopback_request_rejects_non_loopback_host_and_cross_origin(
    tmp_path: Path,
) -> None:
    assert verify_loopback_request("127.0.0.1", {"host": "127.0.0.1:3210"}).ok
    assert verify_loopback_request("127.0.0.1", {"host": "example.com"}).status == 403
    assert (
        verify_loopback_request(
            "127.0.0.1",
            {
                "host": "127.0.0.1:3210",
                "origin": "http://example.com",
            },
        ).status
        == 403
    )


def test_reload_and_shutdown_auth_failures_append_redacted_audits(
    tmp_path: Path,
) -> None:
    FileMaterialStore(tmp_path).init()
    audit_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"
    token = "secret-token-value"

    result = verify_token(
        tmp_path,
        {"authorization": f"Bearer {token}"},
        audit_path=audit_path,
        action="shutdown",
    )

    audits = read_audits(audit_path)
    serialized = json.dumps(audits, sort_keys=True)
    assert result == AuthResult.INVALID
    assert audits[-1]["action"]["name"] == "shutdown"
    assert audits[-1]["action"]["status"] == "denied"
    assert token not in serialized
