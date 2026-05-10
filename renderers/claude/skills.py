from __future__ import annotations

from pathlib import Path

from renderers.codex.skills import render_codex_skill_tree


def render_claude_skill_tree(source_root: Path) -> dict[str, str]:
    """Render shared-skill source files into Claude plugin-relative paths."""

    return render_codex_skill_tree(source_root)
