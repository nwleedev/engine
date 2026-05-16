from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "codex"
    / "shared-subagents"
    / "scripts"
    / "install_shared_subagents.py"
)

PLUGIN_ROOT = SCRIPT_PATH.parents[1]

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

LEGACY_AGENTS = (
    "online-researcher",
    "spec-reviewer",
)


def agent_instructions(agent_name: str) -> str:
    data = tomllib.loads(
        (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").read_text(encoding="utf-8")
    )
    return data["developer_instructions"]


def instruction_block(text: str, start: str, stop: str) -> str:
    """Return the bounded instruction block used to lock agent contracts."""

    assert start in text
    assert stop in text
    return text.split(start, 1)[1].split(stop, 1)[0]


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

    assert len(targets) == len(EXPECTED_AGENTS)
    assert [target.name for target in targets] == [
        f"{agent_name}.toml" for agent_name in EXPECTED_AGENTS
    ]
    assert not (tmp_path / ".codex" / "agents").exists()


def test_install_copies_all_agents(tmp_path: Path) -> None:
    module = load_module()

    targets = module.install_agents(tmp_path, dry_run=False)

    assert len(targets) == len(EXPECTED_AGENTS)
    assert [target.name for target in targets] == [
        f"{agent_name}.toml" for agent_name in EXPECTED_AGENTS
    ]
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


def test_legacy_shared_subagents_are_not_generated() -> None:
    for agent_name in LEGACY_AGENTS:
        assert not (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").exists()

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(PLUGIN_ROOT.rglob("*"))
        if path.is_file() and path.suffix in {".md", ".toml", ".json"}
    )

    for agent_name in LEGACY_AGENTS:
        assert f"`{agent_name}`" not in combined


def test_test_adequacy_reviewer_owns_downstream_test_quality() -> None:
    instructions = agent_instructions("test-adequacy-reviewer")

    assert "downstream project" in instructions
    assert "Acceptance Criteria ID" in instructions
    assert "User Scenario ID" in instructions
    assert "Fixture/Mock Justification" in instructions
    assert "Do not approve tests that assert only mock calls" in instructions


def test_plugin_manifest_exposes_scaffold_skill() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    skill = PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md"

    assert manifest["name"] == "shared-subagents"
    assert manifest["version"] == "0.2.6"
    assert manifest["skills"] == "./skills/"
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


def test_requirements_reviewer_owns_user_requirement_fidelity() -> None:
    instructions = agent_instructions("requirements-reviewer")

    assert "user requirements" in instructions
    assert "acceptance criteria" in instructions
    assert "non-goals" in instructions
    assert "inferred assumptions" in instructions
    assert "Do not inspect unrelated repository files." in instructions


def test_plan_reviewer_owns_plan_executability_and_fallbacks() -> None:
    instructions = agent_instructions("plan-reviewer")

    assert "implementation plan" in instructions
    assert "acceptance criteria" in instructions
    assert "failure handling" in instructions
    assert "fallback" in instructions
    assert "Do not inspect unrelated repository files." in instructions


def test_docs_researcher_includes_comment_format_research_criteria() -> None:
    instructions = agent_instructions("docs-researcher")
    return_block = instruction_block(instructions, "Return:", "Do not make code changes")
    comment_contract = instruction_block(
        return_block,
        "- comment/documentation format findings when requested:",
        "\n\n",
    )

    assert "comment and documentation format requirements" in instructions
    assert "official source" in instructions
    assert "project conventions" in instructions
    assert "target stack and version context" in comment_contract
    assert "official sources checked" in comment_contract
    assert "required comment syntax or schema description field" in comment_contract
    assert "optional tags or sections" in comment_contract
    assert "caveats and project-convention gaps" in comment_contract
    assert "unresolved ambiguity" in comment_contract


def test_code_reviewer_includes_comment_quality_review_criteria() -> None:
    instructions = agent_instructions("code-reviewer")

    assert "comment quality" in instructions
    assert "stale" in instructions
    assert "public/exported API comments" in instructions
    assert "Do not repeat" in instructions
    assert "security/privacy-sensitive comments" in instructions
    assert "generated code" in instructions
    assert "unclear names" in instructions
    assert "oversized expressions" in instructions
    assert "option objects" in instructions
    assert "TODO/FIXME/HACK/NOTE" in instructions
    assert "owner, reason, removal condition, or tracking reference" in instructions


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
    docs_researcher_line = next(
        line for line in block.splitlines() if "`docs-researcher`" in line
    )
    code_reviewer_line = next(
        line for line in block.splitlines() if "`code-reviewer`" in line
    )

    assert "Spawn subagents only when the user explicitly asks" in block
    assert "Use subagents for broad, parallelizable work" in block
    assert "Keep simple or single-file work in the main session" in block
    assert "Do not delegate urgent blocking work" in block
    assert "Do not ask `reviewer` and `code-reviewer` the same question" in block
    assert "official comment/documentation format" in docs_researcher_line
    assert "comment quality" in code_reviewer_line


def test_reviewer_includes_tdd_review_criteria() -> None:
    instructions = agent_instructions("reviewer")

    assert "TDD review checks:" in instructions
    assert "Return TDD review findings with:" in instructions
    assert "TDD evidence" in instructions
    assert "selected test type" in instructions
    assert "observable behavior" in instructions
    assert "unnecessary fixtures" in instructions
    assert "broad fixtures" in instructions
    assert "unused setup fields" in instructions
    assert "fixtures that hide the failure cause" in instructions
    assert "flaky" in instructions
    assert "skipped tests" in instructions
    assert "failing/passing test commands" in instructions
    assert "failing test was written before or alongside" in instructions
    assert "failure, edge, and regression cases" in instructions
    assert "mocks and fakes" in instructions
    assert "external boundaries" in instructions
    assert "sleeps" in instructions
    assert "real external services" in instructions
    assert "unordered assumptions" in instructions
    assert "environment-only success" in instructions
    assert ".only" in instructions
    assert "disabled assertions" in instructions
    assert "snapshot updates without rationale" in instructions


def test_reviewer_limits_documentation_review_to_user_impacting_boundaries() -> None:
    instructions = agent_instructions("reviewer")

    assert "documentation omissions" in instructions
    assert "public API" in instructions
    assert "behavior boundary" in instructions
    assert "migration" in instructions
    assert "configuration" in instructions
    assert "user-visible" in instructions
    assert "Do not dilute findings with style-only commentary" in instructions


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
