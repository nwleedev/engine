"""Protect sensitive paths and values before prompt composition."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


DENIED_PATH_PARTS = frozenset({"secrets", "credentials"})
DENIED_SUFFIXES = (".pem", ".key")
DENIED_NAMES = frozenset({".env"})
SECRET_PATTERNS = (
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
    ("database-url", re.compile(r"\b[a-z]+://[^:\s]+:[^@\s]+@[^ \n]+")),
    (
        "assignment",
        re.compile(
            r"(?im)^([A-Z0-9_]*(SECRET|TOKEN|PASSWORD|KEY)[A-Z0-9_]*\s*=\s*)(.+)$"
        ),
    ),
)


def _normalize(path: str) -> PurePosixPath:
    """Return a POSIX-style path so deny rules behave consistently across OSes."""

    return PurePosixPath(path.replace("\\", "/"))


def is_denied_path(path: str) -> bool:
    """Return whether a path is too sensitive to read into a prompt."""

    normalized = _normalize(path)
    name = normalized.name
    parts = set(normalized.parts)
    return (
        name in DENIED_NAMES
        or name.startswith(".env.")
        or normalized.suffix in DENIED_SUFFIXES
        or bool(parts & DENIED_PATH_PARTS)
    )


def redact_text(text: str) -> str:
    """Replace secret-like values with stable markers before prompt composition."""

    redacted = text
    for label, pattern in SECRET_PATTERNS:
        if label == "assignment":
            redacted = pattern.sub(r"\1[REDACTED:assignment]", redacted)
        else:
            redacted = pattern.sub(f"[REDACTED:{label}]", redacted)
    return redacted
