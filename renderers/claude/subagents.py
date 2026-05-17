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
CLAUDE_EXCLUDED_SUPPORT_PATHS = frozenset(
    {
        "scripts/install_shared_subagents.py",
        "scripts/print_agents_md_block.py",
        "skills/scaffold/SKILL.md",
        "skills/scaffold/scaffold.py",
    }
)


def _render_claude_readme(source_root: Path) -> str:
    """Return Claude-specific shared-subagents README text."""

    readme_source = source_root / "README.md"
    ensure_source_file(ROOT, readme_source)
    relative_source = readme_source.relative_to(ROOT).as_posix()
    return (
        markdown_header(relative_source)
        + "# Shared Subagents\n\n"
        + "Shared Claude Code agent templates rendered from the canonical "
        + "shared-subagents role definitions.\n\n"
        + "## Agent Roles\n\n"
        + "- `context-manager`, `code-mapper`, and `docs-researcher` gather project "
        + "context, code structure, and official documentation evidence.\n"
        + "- `source-researcher`, `requirements-reviewer`, `plan-reviewer`, and "
        + "`citation-verifier` keep source, requirements, plan, traceability, and "
        + "citation checks separate.\n"
        + "- `test-adequacy-reviewer`, `closure-reviewer`, and `risk-reviewer` review "
        + "test quality, verification-gate evidence, residual risk, rollback, fallback, and "
        + "unverifiable items.\n"
        + "- `reviewer`, `code-reviewer`, and `security-auditor` remain separate "
        + "gates for correctness/behavior regression/contract review, "
        + "maintainability/design/readability, and security-audit review.\n\n"
        + "## Claude Bundle Notes\n\n"
        + "- This bundle contains generated Claude agent Markdown files under "
        + "`agents/`.\n"
        + "- Codex-only installer and scaffold helpers are intentionally omitted from "
        + "this Claude bundle.\n"
        + "- Use the plugin through Claude Code's normal plugin loading and agent "
        + "discovery flow.\n"
        + "- If your Claude Code environment discovers plugin-bundled agents directly, "
        + "invoke them by name. If it requires project-local agents, copy the needed "
        + "Markdown files into `.claude/agents/` and restart Claude Code.\n"
        + "- Example: `Use the test-adequacy-reviewer subagent to review tests for "
        + "AC-001 / SCN-001.`\n"
        + "- Keep runtime-specific MCP configuration in the user or project tool "
        + "configuration that owns those servers.\n\n"
        + "## Superpowers Integration\n\n"
        + "Use `references/superpowers-routing.md` for stage routing and fallback "
        + "role guidance when custom agent names are unavailable.\n"
    )


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
    for path in CLAUDE_EXCLUDED_SUPPORT_PATHS:
        files.pop(path, None)
    files["README.md"] = _render_claude_readme(source_root)
    agents_root = source_root / "agents"

    for agent_file in sorted(agents_root.glob("*.toml")):
        files[f"agents/{agent_file.stem}.md"] = render_claude_agent_markdown(agent_file)

    return files


__all__ = ["render_claude_agent_markdown", "render_claude_agent_tree"]
