from __future__ import annotations

from pathlib import Path

from renderers.shared_subagents import render_shared_subagents_support_tree
from tools.build.headers import python_header
from tools.build.paths import ROOT


def _render_toml_file(path: Path) -> str:
    """Return a generated TOML file body with its canonical source header."""

    if not path.is_file():
        raise ValueError(f"expected file: {path}")

    relative_source = path.relative_to(ROOT).as_posix()
    return python_header(relative_source) + path.read_text(encoding="utf-8")


def render_codex_agent_tree(source_root: Path) -> dict[str, str]:
    """Render the complete canonical shared-subagents tree for Codex."""

    files = render_shared_subagents_support_tree(source_root)
    agents_root = source_root / "agents"

    for agent_file in sorted(agents_root.glob("*.toml")):
        files[f"agents/{agent_file.name}"] = _render_toml_file(agent_file)

    return files


__all__ = ["render_codex_agent_tree"]
