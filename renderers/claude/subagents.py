from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from renderers.shared_subagents import render_shared_subagents_support_tree
from tools.build.headers import markdown_header
from tools.build.paths import ROOT
from tools.build.source_files import ensure_source_file


READ_ONLY_TOOLS = ("Read", "Grep", "Glob")
EDIT_TOOLS = ("Read", "Grep", "Glob", "Edit")


def _tools_for_sandbox(sandbox_mode: str) -> tuple[str, ...]:
    """Map a Codex sandbox mode onto Claude plugin agent tool names."""

    if sandbox_mode == "read-only":
        return READ_ONLY_TOOLS
    return EDIT_TOOLS


def _yaml_quoted_string(value: Any) -> str:
    """Return a YAML 1.2-safe double-quoted string scalar."""

    return json.dumps(str(value))


def _load_agent(path: Path) -> dict[str, Any]:
    """Load a canonical shared-subagent TOML file."""

    ensure_source_file(ROOT, path)
    with path.open("rb") as agent_file:
        return tomllib.load(agent_file)


def render_claude_agent_markdown(path: Path) -> str:
    """Render a canonical shared-subagent TOML file as a Claude agent Markdown file."""

    data = _load_agent(path)
    relative_source = path.relative_to(ROOT).as_posix()
    tools = _tools_for_sandbox(str(data.get("sandbox_mode", "")))
    tool_lines = "\n".join(f"- {tool}" for tool in tools)

    return (
        markdown_header(relative_source)
        + "---\n"
        + f"name: {_yaml_quoted_string(data['name'])}\n"
        + f"description: {_yaml_quoted_string(data['description'])}\n"
        + f"model: {_yaml_quoted_string(data['model'])}\n"
        + "tools:\n"
        + f"{tool_lines}\n"
        + "---\n\n"
        + str(data["developer_instructions"]).rstrip()
        + "\n"
    )


def render_claude_agent_tree(source_root: Path) -> dict[str, str]:
    """Render the complete canonical shared-subagents tree for Claude."""

    files = render_shared_subagents_support_tree(source_root)
    agents_root = source_root / "agents"

    for agent_file in sorted(agents_root.glob("*.toml")):
        files[f"agents/{agent_file.stem}.md"] = render_claude_agent_markdown(agent_file)

    return files


__all__ = ["render_claude_agent_markdown", "render_claude_agent_tree"]
