from __future__ import annotations

from pathlib import Path

from tools.build.headers import markdown_header
from tools.build.paths import ROOT
from tools.build.source_files import ensure_source_file


def _render_markdown_file(path: Path) -> str:
    """Return a generated Markdown file body with its canonical source header."""

    ensure_source_file(ROOT, path)
    relative_source = path.relative_to(ROOT).as_posix()
    return markdown_header(relative_source) + path.read_text(encoding="utf-8")


def render_codex_skill_tree(source_root: Path) -> dict[str, str]:
    """Render shared-skill source files into Codex plugin-relative paths."""

    files: dict[str, str] = {}
    readme = source_root / "README.md"
    skills_root = source_root / "skills"
    references_root = source_root / "references"

    if readme.exists():
        files["README.md"] = _render_markdown_file(readme)

    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        files[f"skills/{skill_file.parent.name}/SKILL.md"] = _render_markdown_file(skill_file)

    for reference_file in sorted(references_root.glob("*.md")):
        files[f"references/{reference_file.name}"] = _render_markdown_file(reference_file)

    return files
