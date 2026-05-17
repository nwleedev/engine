from __future__ import annotations

import pytest

from learnable.core.redaction import redact_text


@pytest.mark.parametrize(
    ("text", "neutral_text"),
    [
        ("Summarize TOKEN=learnable-token-12345 and keep the title.", "keep the title"),
        ("event auth token: learnable-token-12345 for lesson start", "lesson start"),
        ("audit path=.codex/materials/private/module.md status=read", "status=read"),
        ("HTTP 500 body: Bearer learnable-token-12345 was rejected", "HTTP 500 body"),
        ("command failed with LEARNABLE_API_KEY=learnable-token-12345", "command failed"),
        ("server log opened /repo/.codex/materials/private/module.md", "server log"),
    ],
)
def test_redact_text_covers_learnable_output_boundaries(
    text: str, neutral_text: str
) -> None:
    redacted = redact_text(text)

    assert "learnable-token-12345" not in redacted
    assert ".codex/materials/private" not in redacted
    assert neutral_text in redacted


def test_redact_text_hides_dotenv_values_and_bearer_secrets() -> None:
    text = "\n".join(
        [
            "Neutral heading stays visible",
            "PASSWORD=plain-text-secret",
            "Authorization: Bearer bearer-secret-12345",
            "Read .env.local for setup",
        ]
    )

    redacted = redact_text(text)

    assert "Neutral heading stays visible" in redacted
    assert "plain-text-secret" not in redacted
    assert "bearer-secret-12345" not in redacted
    assert ".env.local" not in redacted
    assert "[REDACTED:assignment]" in redacted
    assert "[REDACTED:bearer]" in redacted
    assert "[REDACTED:path]" in redacted


def test_redact_text_preserves_neutral_text() -> None:
    text = "Lesson draft uses tokenized examples and a keynote outline."

    assert redact_text(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "MONKEY=banana",
        "DONKEY=banana",
        "API_MONKEY=banana",
    ],
)
def test_redact_text_preserves_assignment_keys_with_sensitive_substrings(
    text: str,
) -> None:
    assert redact_text(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "SESSION_TOKEN=session-token-12345",
        "OPENAI_API_KEY=api-key-12345",
        "PASSWORD=plain-text-secret",
        "SECRET=plain-text-secret",
    ],
)
def test_redact_text_redacts_sensitive_assignment_key_tokens(text: str) -> None:
    redacted = redact_text(text)

    assert text.split("=", maxsplit=1)[1] not in redacted
    assert "[REDACTED:assignment]" in redacted
