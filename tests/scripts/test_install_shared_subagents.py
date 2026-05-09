from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "shared-subagents"
    / "scripts"
    / "install_shared_subagents.py"
)

PLUGIN_ROOT = SCRIPT_PATH.parents[1]


def load_module():
    """Load the install script as a test module."""

    spec = importlib.util.spec_from_file_location("install_shared_subagents", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_returns_expected_targets(tmp_path: Path) -> None:
    module = load_module()

    targets = module.install_agents(tmp_path, dry_run=True)

    assert len(targets) == 8
    assert targets[0] == tmp_path / ".codex" / "agents" / "context-manager.toml"
    assert not (tmp_path / ".codex" / "agents").exists()


def test_install_copies_all_agents(tmp_path: Path) -> None:
    module = load_module()

    targets = module.install_agents(tmp_path, dry_run=False)

    assert len(targets) == 8
    for target in targets:
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "# shared-subagents:provided-agent" in text
        assert "developer_instructions" in text


def test_install_refuses_to_overwrite_existing_agent(tmp_path: Path) -> None:
    module = load_module()
    existing = tmp_path / ".codex" / "agents" / "context-manager.toml"
    existing.parent.mkdir(parents=True)
    existing.write_text("custom local agent\n", encoding="utf-8")

    try:
        module.install_agents(tmp_path, dry_run=False)
    except FileExistsError as error:
        assert "context-manager.toml" in str(error)
    else:
        raise AssertionError("install_agents should reject existing files by default")

    assert existing.read_text(encoding="utf-8") == "custom local agent\n"


def test_backup_preserves_existing_agent_before_install(tmp_path: Path) -> None:
    module = load_module()
    existing = tmp_path / ".codex" / "agents" / "context-manager.toml"
    existing.parent.mkdir(parents=True)
    existing.write_text("custom local agent\n", encoding="utf-8")

    targets = module.install_agents(tmp_path, dry_run=False, backup=True)

    backup = tmp_path / ".codex" / "agents" / "context-manager.toml.bak"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "custom local agent\n"
    assert existing.read_text(encoding="utf-8") != "custom local agent\n"
    assert targets[0] == existing


def test_plugin_manifest_exposes_scaffold_skill() -> None:
    manifest = (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(
        encoding="utf-8"
    )
    skill = PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md"

    assert '"name": "shared-subagents"' in manifest
    assert '"version": "0.2.1"' in manifest
    assert '"skills": "./skills/"' in manifest
    assert skill.exists()
    assert "name: scaffold" in skill.read_text(encoding="utf-8")


def test_scaffold_skill_references_shared_scripts() -> None:
    text = (
        PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "skills/scaffold/scaffold.py --dry-run" in text
    assert "skills/scaffold/scaffold.py --print-agents-md-block" in text
    assert "--project-root" in text
    assert ".codex/agents" in text
    assert "Does not modify AGENTS.md automatically." in text
    assert "real Codex home" not in text


def test_scaffold_wrapper_exists() -> None:
    assert (PLUGIN_ROOT / "skills" / "scaffold" / "scaffold.py").exists()


def test_readme_uses_skill_relative_scaffold_command() -> None:
    readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    assert "python3 /path/to/shared-subagents/skills/scaffold/scaffold.py" in readme
    assert "plugins/shared-subagents/scripts/install_shared_subagents.py" not in readme
    assert ".codex/agents" in readme
    assert "~/.codex/agents" not in readme


def test_spec_reviewer_is_bounded_for_small_reviews() -> None:
    text = (PLUGIN_ROOT / "agents" / "spec-reviewer.toml").read_text(
        encoding="utf-8"
    )

    assert 'model_reasoning_effort = "medium"' in text
    assert "For small scoped reviews:" in text
    assert "Return at most 5 findings." in text
    assert "Do not inspect unrelated repository files." in text


def test_readme_documents_mcp_inheritance_without_owning_mcp_config() -> None:
    readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    assert "MCP inheritance" in readme
    assert "~/.codex/config.toml" in readme
    assert "shared-subagents does not install or modify MCP servers" in readme
    assert "startup_timeout_sec" in readme
    assert "required = false" in readme


def test_agents_md_block_warns_about_global_mcp_startup_cost() -> None:
    block = (PLUGIN_ROOT / "references" / "agents-md-block.md").read_text(
        encoding="utf-8"
    )

    assert "Global MCP servers may be inherited by spawned subagents" in block
    assert "project-local `.codex/agents`" in block
    assert "project `.codex/config.toml`" in block


def test_agents_md_block_defines_subagent_use_boundaries() -> None:
    block = (PLUGIN_ROOT / "references" / "agents-md-block.md").read_text(
        encoding="utf-8"
    )

    assert "Spawn subagents only when the user explicitly asks" in block
    assert "Use subagents for broad, parallelizable work" in block
    assert "Keep simple or single-file work in the main session" in block
    assert "Do not delegate urgent blocking work" in block
    assert "Do not ask `reviewer` and `code-reviewer` the same question" in block


def test_reviewer_includes_tdd_review_criteria() -> None:
    text = (PLUGIN_ROOT / "agents" / "reviewer.toml").read_text(
        encoding="utf-8"
    )

    assert "TDD review checks:" in text
    assert "Return TDD review findings with:" in text
    assert "TDD evidence" in text
    assert "selected test type" in text
    assert "observable behavior" in text
    assert "unnecessary fixtures" in text
    assert "broad fixtures" in text
    assert "unused setup fields" in text
    assert "fixtures that hide the failure cause" in text
    assert "flaky" in text
    assert "skipped tests" in text
    assert "failing/passing test commands" in text
    assert "failing test was written before or alongside" in text
    assert "failure, edge, and regression cases" in text
    assert "mocks and fakes" in text
    assert "external boundaries" in text
    assert "sleeps" in text
    assert "real external services" in text
    assert "unordered assumptions" in text
    assert "environment-only success" in text
    assert ".only" in text
    assert "disabled assertions" in text
    assert "snapshot updates without rationale" in text


def test_agents_md_block_routes_tdd_review_to_reviewer() -> None:
    block = (PLUGIN_ROOT / "references" / "agents-md-block.md").read_text(
        encoding="utf-8"
    )

    reviewer_lines = [line for line in block.splitlines() if "`reviewer`" in line]
    assert any(
        "TDD" in line
        and "evidence" in line
        and "test adequacy" in line
        and "test-writing" in line
        for line in reviewer_lines
    )
