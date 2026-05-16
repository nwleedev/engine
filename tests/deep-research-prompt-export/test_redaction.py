from __future__ import annotations

from research_prompt.redaction import is_denied_path, redact_text


def test_denies_secret_paths() -> None:
    assert is_denied_path(".env")
    assert is_denied_path(".env.local")
    assert is_denied_path("secrets/prod.json")
    assert is_denied_path("credentials/service-account.json")
    assert is_denied_path("certs/private.pem")
    assert is_denied_path("keys/app.key")


def test_allows_normal_source_paths() -> None:
    assert not is_denied_path("src/app.py")
    assert not is_denied_path("packages/web/package.json")


def test_redacts_secret_like_values() -> None:
    source = "\n".join(
        [
            "OPENAI_API_KEY=sk-test_abcdefghijklmnopqrstuvwxyz123456",
            "DATABASE_URL=postgres://user:pass@example.com:5432/app",
            "SESSION_TOKEN=secret-session-token-value",
            "const jwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature'",
        ]
    )

    redacted = redact_text(source)

    assert "sk-test_" not in redacted
    assert "postgres://user:pass@" not in redacted
    assert "secret-session-token-value" not in redacted
    assert "eyJhbGciOi" not in redacted
    assert "[REDACTED:" in redacted
