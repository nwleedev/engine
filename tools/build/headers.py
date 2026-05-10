from __future__ import annotations


GENERATED_NOTICE = "GENERATED FILE - DO NOT EDIT"


def markdown_header(source: str) -> str:
    """Return a Markdown generated-file header for a canonical source path."""

    return f"<!-- {GENERATED_NOTICE} -->\n<!-- source: {source} -->\n\n"


def python_header(source: str) -> str:
    """Return a Python generated-file header for a canonical source path."""

    return f"# {GENERATED_NOTICE}\n# source: {source}\n\n"
