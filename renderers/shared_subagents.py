from __future__ import annotations

from pathlib import Path

from tools.build.headers import markdown_header, python_header
from tools.build.paths import ROOT


def _render_support_file(path: Path) -> str:
    """Return a generated support file body with the correct header type."""

    relative_source = path.relative_to(ROOT).as_posix()
    body = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        return markdown_header(relative_source) + body
    if path.suffix == ".py":
        return python_header(relative_source) + body
    raise ValueError(f"unsupported shared-subagents support file: {path}")


def render_shared_subagents_support_tree(source_root: Path) -> dict[str, str]:
    """Render non-agent shared-subagents plugin files into relative paths."""

    files: dict[str, str] = {}
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if "agents" in path.relative_to(source_root).parts:
            continue
        relative_path = path.relative_to(source_root).as_posix()
        files[relative_path] = _render_support_file(path)
    return files


__all__ = ["render_shared_subagents_support_tree"]
