from __future__ import annotations

import re


_SECRET_PATTERNS = (
    (
        "assignment",
        re.compile(r"(?i)\b([A-Z0-9_]+)(\s*=\s*)([^\s,;]+)"),
    ),
    (
        "bearer",
        re.compile(r"(?i)\b(Bearer\s+)([A-Za-z0-9._~+/=-]{8,})"),
    ),
    (
        "labeled-secret",
        re.compile(
            r"(?i)\b((?:api[_-]?key|password|secret|token)\s*[:=]\s*)(?!\[REDACTED:)([^\s,;]+)"
        ),
    ),
    (
        "path",
        re.compile(r"(?i)(?:^|(?<=\s))\S*\.codex[/\\]materials[/\\]\S+"),
    ),
    (
        "path",
        re.compile(r"(?i)(?:^|(?<=\s))\S*\.env(?:\.[A-Za-z0-9_.-]+)?"),
    ),
)

_SENSITIVE_ASSIGNMENT_TOKENS = frozenset({"key", "password", "secret", "token"})


def redact_text(text: str) -> str:
    redacted = text
    for label, pattern in _SECRET_PATTERNS:
        if label == "assignment":
            redacted = pattern.sub(_redact_assignment, redacted)
        elif label == "bearer":
            redacted = pattern.sub(r"\1[REDACTED:bearer]", redacted)
        elif label == "labeled-secret":
            redacted = pattern.sub(r"\1[REDACTED:secret]", redacted)
        else:
            redacted = pattern.sub("[REDACTED:path]", redacted)
    return redacted


def _redact_assignment(match: re.Match[str]) -> str:
    key = match.group(1)
    if not _is_sensitive_assignment_key(key):
        return match.group(0)
    return f"{key}{match.group(2)}[REDACTED:assignment]"


def _is_sensitive_assignment_key(key: str) -> bool:
    tokens = {token for token in key.lower().split("_") if token}
    return bool(tokens & _SENSITIVE_ASSIGNMENT_TOKENS)
