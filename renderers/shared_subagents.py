from __future__ import annotations

from pathlib import Path

from tools.build.headers import markdown_header, python_header
from tools.build.paths import ROOT
from tools.build.source_files import ensure_source_file


def _render_skill_markdown(path: Path, header: str, body: str) -> str:
    """Return SKILL.md text with generated tracing after YAML frontmatter."""

    marker = "---\n"
    if not body.startswith(marker):
        raise ValueError(f"missing YAML frontmatter: {path}")

    end = body.find(f"\n{marker}", len(marker))
    if end == -1:
        raise ValueError(f"unterminated YAML frontmatter: {path}")

    frontmatter_end = end + len(f"\n{marker}")
    return body[:frontmatter_end] + header + body[frontmatter_end:]


def _is_skill_manifest(path: Path, source_root: Path) -> bool:
    """Return whether the support file is a skill manifest."""

    relative_parts = path.relative_to(source_root).parts
    return (
        path.name == "SKILL.md"
        and len(relative_parts) == 3
        and relative_parts[0] == "skills"
    )


def _render_support_file(path: Path, source_root: Path) -> str:
    """Return a generated support file body with the correct header type."""

    ensure_source_file(ROOT, path)
    relative_source = path.relative_to(ROOT).as_posix()
    body = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        header = markdown_header(relative_source)
        if _is_skill_manifest(path, source_root):
            return _render_skill_markdown(path, header, body)
        return header + body
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
        files[relative_path] = _render_support_file(path, source_root)
    return files


__all__ = ["render_shared_subagents_support_tree"]
