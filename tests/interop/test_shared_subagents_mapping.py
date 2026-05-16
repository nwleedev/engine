from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

import renderers.claude.subagents as claude_subagents
from renderers.claude.subagents import (
    render_claude_agent_markdown,
    render_claude_agent_tree,
)
from renderers.codex.subagents import render_codex_agent_tree
from tools.build.headers import markdown_header, python_header


EXPECTED_AGENTS = (
    "context-manager",
    "code-mapper",
    "docs-researcher",
    "source-researcher",
    "requirements-reviewer",
    "plan-reviewer",
    "citation-verifier",
    "test-adequacy-reviewer",
    "closure-reviewer",
    "risk-reviewer",
    "reviewer",
    "code-reviewer",
    "security-auditor",
)


def test_claude_agent_markdown_maps_codex_read_only_agent_fields() -> None:
    source = ROOT / "plugin-sources" / "shared-subagents" / "agents" / "code-mapper.toml"

    text = render_claude_agent_markdown(source)

    assert text.startswith(
        markdown_header("plugin-sources/shared-subagents/agents/code-mapper.toml")
    )
    assert 'name: "code-mapper"' in text
    assert "tools:" in text
    assert "- Read" in text
    assert "- Grep" in text
    assert "- Glob" in text
    assert "Stay in exploration mode." in text


def test_claude_agent_markdown_preserves_test_adequacy_role_contract() -> None:
    source = (
        ROOT
        / "plugin-sources"
        / "shared-subagents"
        / "agents"
        / "test-adequacy-reviewer.toml"
    )

    text = render_claude_agent_markdown(source)

    assert 'name: "test-adequacy-reviewer"' in text
    assert "Fixture/Mock Justification" in text
    assert "downstream project" in text


def test_codex_agent_tree_adds_generated_header_and_preserves_original_body() -> None:
    files = render_codex_agent_tree(ROOT / "plugin-sources" / "shared-subagents")
    source = ROOT / "plugin-sources" / "shared-subagents" / "agents" / "code-mapper.toml"
    original_body = source.read_text(encoding="utf-8")

    text = files["agents/code-mapper.toml"]

    assert text.startswith(
        python_header("plugin-sources/shared-subagents/agents/code-mapper.toml")
    )
    assert original_body in text


def test_codex_agent_tree_includes_complete_plugin_support_files() -> None:
    files = render_codex_agent_tree(ROOT / "plugin-sources" / "shared-subagents")

    assert "README.md" in files
    assert "references/agents-md-block.md" in files
    assert "skills/scaffold/SKILL.md" in files
    assert "skills/scaffold/scaffold.py" in files
    assert "scripts/install_shared_subagents.py" in files
    assert files["skills/scaffold/SKILL.md"].startswith("---\n")
    assert (
        "\n---\n"
        + markdown_header("plugin-sources/shared-subagents/skills/scaffold/SKILL.md")
        in files["skills/scaffold/SKILL.md"]
    )
    assert files["README.md"].startswith(
        markdown_header("plugin-sources/shared-subagents/README.md")
    )
    assert files["scripts/install_shared_subagents.py"].startswith(
        python_header("plugin-sources/shared-subagents/scripts/install_shared_subagents.py")
    )


def test_claude_agent_tree_excludes_codex_scaffold_support() -> None:
    files = render_claude_agent_tree(ROOT / "plugin-sources" / "shared-subagents")

    assert "scripts/install_shared_subagents.py" not in files
    assert "scripts/print_agents_md_block.py" not in files
    assert "skills/scaffold/SKILL.md" not in files
    assert "skills/scaffold/scaffold.py" not in files


def test_claude_generated_bundle_does_not_advertise_codex_install_surface() -> None:
    readme = (
        ROOT / "plugins" / "claude" / "shared-subagents" / "README.md"
    ).read_text(encoding="utf-8")

    assert ".codex/agents" not in readme
    assert ".toml" not in readme
    assert "restart Codex" not in readme
    assert "install_shared_subagents.py" not in readme
    assert "print_agents_md_block.py" not in readme
    assert "skills/scaffold/scaffold.py" not in readme


def test_claude_generated_bundle_contains_expected_agents_only() -> None:
    agents_root = ROOT / "plugins" / "claude" / "shared-subagents" / "agents"
    generated_agents = sorted(path.name for path in agents_root.glob("*.md"))

    assert generated_agents == sorted(f"{agent_name}.md" for agent_name in EXPECTED_AGENTS)
    assert "online-researcher.md" not in generated_agents
    assert "spec-reviewer.md" not in generated_agents


def test_claude_generated_bundle_excludes_codex_scaffold_files() -> None:
    plugin_root = ROOT / "plugins" / "claude" / "shared-subagents"

    assert not (plugin_root / "scripts" / "install_shared_subagents.py").exists()
    assert not (plugin_root / "scripts" / "print_agents_md_block.py").exists()
    assert not (plugin_root / "skills" / "scaffold" / "SKILL.md").exists()
    assert not (plugin_root / "skills" / "scaffold" / "scaffold.py").exists()


def test_claude_agent_frontmatter_quotes_string_scalars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    source = agents / "quoted.toml"
    source.write_text(
        '\n'.join(
            [
                'name = "agent:with \\"quotes\\""',
                'description = "first line: with colon\\nsecond line \\"quoted\\""',
                'model = "claude:model"',
                'sandbox_mode = "read-only"',
                'developer_instructions = "Use the quoted frontmatter."',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(claude_subagents, "ROOT", tmp_path)

    text = render_claude_agent_markdown(source)

    assert f"name: {json.dumps('agent:with \"quotes\"')}" in text
    assert (
        "description: "
        + json.dumps('first line: with colon\nsecond line "quoted"')
        in text
    )
    assert f"model: {json.dumps('claude:model')}" in text


def test_claude_agent_non_read_only_sandbox_allows_edit_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    source = agents / "editable.toml"
    source.write_text(
        '\n'.join(
            [
                'name = "editable-agent"',
                'description = "May edit files"',
                'model = "claude-sonnet"',
                'sandbox_mode = "workspace-write"',
                'developer_instructions = "Edit when asked."',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(claude_subagents, "ROOT", tmp_path)

    text = render_claude_agent_markdown(source)

    assert "- Read" in text
    assert "- Grep" in text
    assert "- Glob" in text
    assert "- Edit" in text
