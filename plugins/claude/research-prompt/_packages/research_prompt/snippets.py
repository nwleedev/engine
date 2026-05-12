"""Extract bounded source excerpts for prompt context."""

from __future__ import annotations

from pathlib import Path

from .redaction import redact_text


MAX_EXCERPT_CHARS = 4000


def extract_excerpt(path: Path, *, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    """Read a bounded text excerpt from a source file and redact secrets."""

    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED: excerpt exceeded budget]"
    return redact_text(text)
