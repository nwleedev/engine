"""Extract bounded source excerpts for prompt context."""

from __future__ import annotations

from pathlib import Path

from .redaction import redact_text


MAX_EXCERPT_CHARS = 4000


def extract_excerpt(
    path: Path,
    *,
    line: int | None = None,
    context_lines: int = 4,
    max_chars: int = MAX_EXCERPT_CHARS,
) -> str:
    """Read a bounded text excerpt from a source file and redact secrets."""

    text = path.read_text(encoding="utf-8", errors="replace")
    if line is not None:
        lines = text.splitlines()
        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)
        text = "\n".join(lines[start:end]) + "\n"
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED: excerpt exceeded budget]"
    return redact_text(text)
