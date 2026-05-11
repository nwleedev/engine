from __future__ import annotations

from pathlib import Path

from tools.build.headers import markdown_header, python_header
from tools.build.paths import ROOT
from tools.build.source_files import ensure_source_file


def _read_generated_file(path: Path, header: str) -> str:
    """Return a generated text file body with the provided header."""

    ensure_source_file(ROOT, path)
    return header + path.read_text(encoding="utf-8")


def _read_generated_skill_file(path: Path, header: str) -> str:
    """Return generated SKILL.md text while keeping YAML frontmatter first."""

    ensure_source_file(ROOT, path)
    text = path.read_text(encoding="utf-8")
    marker = "---\n"
    if not text.startswith(marker):
        raise ValueError(f"missing YAML frontmatter: {path}")

    end = text.find(f"\n{marker}", len(marker))
    if end == -1:
        raise ValueError(f"unterminated YAML frontmatter: {path}")

    frontmatter_end = end + len(f"\n{marker}")
    return text[:frontmatter_end] + header + text[frontmatter_end:]


def _source_path(path: Path) -> str:
    """Return a repository-relative canonical source path."""

    return path.relative_to(ROOT).as_posix()


def _render_markdown(path: Path) -> str:
    """Render a Markdown source file with a generated source annotation."""

    source = _source_path(path)
    return _read_generated_file(path, markdown_header(source))


def _render_skill_markdown(path: Path) -> str:
    """Render a skill manifest with source annotation after frontmatter."""

    source = _source_path(path)
    return _read_generated_skill_file(path, markdown_header(source))


def _render_python(path: Path) -> str:
    """Render a Python helper source file with a generated source annotation."""

    source = _source_path(path)
    return _read_generated_file(path, python_header(source))


def _is_python_helper(path: Path, source_root: Path) -> bool:
    """Return whether a Python file is a skill-local scripts helper."""

    relative_parts = path.relative_to(source_root).parts
    return (
        path.suffix == ".py"
        and len(relative_parts) >= 4
        and relative_parts[0] == "skills"
        and path.parent.name == "scripts"
    )


def _is_skill_manifest(path: Path, source_root: Path) -> bool:
    """Return whether a file is a skill manifest under the source tree."""

    relative_parts = path.relative_to(source_root).parts
    return (
        path.name == "SKILL.md"
        and len(relative_parts) == 3
        and relative_parts[0] == "skills"
    )


def _render_supported_file(path: Path, source_root: Path) -> str:
    """Render a supported plugin source file or fail on source drift."""

    if path.suffix == ".md":
        if _is_skill_manifest(path, source_root):
            return _render_skill_markdown(path)
        return _render_markdown(path)
    if _is_python_helper(path, source_root):
        return _render_python(path)

    relative_path = path.relative_to(source_root).as_posix()
    raise ValueError(f"unsupported plugin source file: {relative_path}")


def render_plugin_text_tree(source_root: Path) -> dict[str, str]:
    """Render supported plugin source files into plugin-relative paths."""

    files: dict[str, str] = {}

    for source_file in sorted(source_root.rglob("*")):
        if source_file.is_dir():
            continue
        relative_path = source_file.relative_to(source_root).as_posix()
        files[relative_path] = _render_supported_file(source_file, source_root)

    return files


__all__ = ["render_plugin_text_tree"]
