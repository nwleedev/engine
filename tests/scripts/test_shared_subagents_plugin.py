from __future__ import annotations

import json
import importlib.util
import tomllib
from pathlib import Path


PLUGIN_ROOT = (
    Path(__file__).resolve().parents[2] / "plugins" / "codex" / "shared-subagents"
)
ROOT = Path(__file__).resolve().parents[2]
SHARED_SUBAGENTS_BLOCK = ROOT / "docs" / "shared-subagents" / "AGENTS.block.md"

EXPECTED_AGENTS = (
    "context-manager",
    "code-mapper",
    "docs-researcher",
    "source-researcher",
    "requirements-reviewer",
    "plan-reviewer",
    "spec-coverage-reviewer",
    "citation-verifier",
    "test-adequacy-reviewer",
    "closure-reviewer",
    "completion-claim-reviewer",
    "risk-reviewer",
    "reviewer",
    "code-reviewer",
    "security-auditor",
)

LEGACY_AGENTS = (
    "online-researcher",
    "spec-reviewer",
)

ACTIVE_ROUTE_DOCS = (
    SHARED_SUBAGENTS_BLOCK,
    PLUGIN_ROOT / "references" / "superpowers-routing.md",
    PLUGIN_ROOT / "README.md",
)


def agent_instructions(agent_name: str) -> str:
    data = tomllib.loads(
        (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").read_text(encoding="utf-8")
    )
    return data["developer_instructions"]


def agent_data(agent_name: str) -> dict[str, object]:
    return tomllib.loads(
        (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").read_text(encoding="utf-8")
    )


def instruction_block(text: str, start: str, stop: str) -> str:
    """Return the bounded instruction block used to lock agent contracts."""

    assert start in text
    assert stop in text
    return text.split(start, 1)[1].split(stop, 1)[0]


def load_install_module():
    """Load the generated install helper as a test module."""

    script = PLUGIN_ROOT / "skills" / "install" / "install.py"
    spec = importlib.util.spec_from_file_location("shared_subagents_install", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_bundle_contains_expected_agents() -> None:
    generated_agents = sorted(path.name for path in (PLUGIN_ROOT / "agents").glob("*.toml"))

    assert generated_agents == sorted(f"{agent_name}.toml" for agent_name in EXPECTED_AGENTS)
    for agent_name in EXPECTED_AGENTS:
        text = (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").read_text(
            encoding="utf-8"
        )
        assert "# shared-subagents:provided-agent" in text
        assert "developer_instructions" in text


def test_legacy_shared_subagents_are_not_generated() -> None:
    for agent_name in LEGACY_AGENTS:
        assert not (PLUGIN_ROOT / "agents" / f"{agent_name}.toml").exists()


def test_legacy_shared_subagents_are_absent_from_active_route_docs() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_ROUTE_DOCS)

    for agent_name in LEGACY_AGENTS:
        assert f"`{agent_name}`" not in combined


def test_test_adequacy_reviewer_owns_downstream_test_quality() -> None:
    data = agent_data("test-adequacy-reviewer")
    instructions = data["developer_instructions"]
    check_block = instruction_block(instructions, "Check:", "Return findings first")
    do_not_block = instruction_block(
        instructions,
        "Do not approve",
        "Do not make code changes.",
    )

    assert "downstream project" in data["description"]
    for term in (
        "Acceptance Criteria ID",
        "User Scenario ID",
        "linked_spec_clause_ids",
        "Fixture/Mock Justification",
        "Fixture Governance Contract",
        "fixture budget",
        "high-fidelity boundary",
        "fixture_overgrowth",
        "stale_fixture",
        "missing_real_boundary_check",
        "unjustified_fixture",
        "test_only_behavior",
        "failed, skipped, or not-run test commands",
    ):
        assert term in check_block
    assert "tests that assert only mock calls" in do_not_block
    assert "fixture-heavy tests without Fixture Governance Contract evidence" in do_not_block


def test_spec_coverage_reviewer_owns_spec_clause_coverage() -> None:
    instructions = agent_instructions("spec-coverage-reviewer")
    check_block = instruction_block(instructions, "Check:", "Return findings first")
    do_not_block = instruction_block(
        instructions,
        "Do not inspect",
        "Do not make code changes.",
    )

    for term in (
        "Spec Ledger",
        "Spec-to-Plan Coverage Matrix",
        "spec_clause_id",
        "source_location",
        "linked_spec_clause_ids",
        "validation_intent",
        "coverage_status",
        "missing_plan",
        "missing_validation",
        "missing_evidence",
        "stale_evidence",
        "unresolved_risk",
        "Fixture Governance Contract",
        "confidential source text is redacted",
    ):
        assert term in check_block
    assert "raw full spec" not in check_block
    assert "raw full spec" in do_not_block
    assert "Do not approve coverage from broad SPEC IDs alone" in do_not_block


def test_completion_claim_reviewer_requires_validator_and_boundary_evidence() -> None:
    instructions = agent_instructions("completion-claim-reviewer")
    check_block = instruction_block(instructions, "Check:", "Return findings first")
    do_not_block = instruction_block(
        instructions,
        "Do not approve",
        "Do not make code changes.",
    )

    for term in (
        "Coverage Report",
        "Verification Gate",
        "Evidence Bundle",
        "missing_plan",
        "missing_validation",
        "missing_evidence",
        "stale_evidence",
        "unresolved_risk",
        "fixture_overgrowth",
        "stale_fixture",
        "missing_real_boundary_check",
        "unjustified_fixture",
        "test_only_behavior",
        "machine-readable JSON",
        "redacted Markdown",
        "validator exit code",
        "validator command",
        "validator report path",
        "not-run commands",
        "skipped checks",
    ):
        assert term in check_block
    assert "Do not approve done when required evidence is missing" in do_not_block


def test_superpowers_routing_includes_spec_coverage_and_completion_reviewers() -> None:
    routing = (
        PLUGIN_ROOT / "references" / "superpowers-routing.md"
    ).read_text(encoding="utf-8")

    assert "| spec coverage review | `spec-coverage-reviewer` |" in routing
    assert "| completion claim review | `completion-claim-reviewer` |" in routing
    assert "Coverage Report, Verification Gate, and Evidence Bundle" in routing
    assert "Do not use `plan-reviewer` as a substitute for `spec-coverage-reviewer`" in routing
    assert (
        "Do not use `closure-reviewer` as a substitute for `completion-claim-reviewer`"
        in routing
    )


def test_plugin_manifest_exposes_install_skill() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert manifest["name"] == "shared-subagents"
    assert manifest["version"] == "0.3.1"
    assert manifest["skills"] == "./skills/"
    assert (PLUGIN_ROOT / "skills" / "install" / "SKILL.md").exists()
    assert (PLUGIN_ROOT / "skills" / "install" / "install.py").exists()
    assert not (PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md").exists()
    assert not (PLUGIN_ROOT / "skills" / "scaffold" / "scaffold.py").exists()
    assert not (PLUGIN_ROOT / "scripts" / "install_shared_subagents.py").exists()
    assert not (PLUGIN_ROOT / "scripts" / "print_agents_md_block.py").exists()


def test_readme_documents_agent_bundle_without_scaffold_flow() -> None:
    readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    assert "plugin-bundled agents" in readme
    assert "$shared-subagents:install" in readme
    assert "AGENTS.block.md" not in readme
    assert "skills/scaffold/scaffold.py" not in readme
    assert "install_shared_subagents.py" not in readme
    assert "Use `$shared-subagents:scaffold`" not in readme


def test_install_skill_dry_run_targets_project_local_agents(tmp_path: Path) -> None:
    module = load_install_module()

    targets = module.install_agents(tmp_path, dry_run=True)

    assert len(targets) == len(EXPECTED_AGENTS)
    assert [target.name for target in targets] == [
        f"{agent_name}.toml" for agent_name in EXPECTED_AGENTS
    ]
    assert targets[0].parent == tmp_path / ".codex" / "agents"
    assert not (tmp_path / ".codex" / "agents").exists()


def test_install_skill_copies_agents_and_refuses_overwrite(tmp_path: Path) -> None:
    module = load_install_module()

    targets = module.install_agents(tmp_path, dry_run=False)

    assert len(targets) == len(EXPECTED_AGENTS)
    for target in targets:
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "# shared-subagents:provided-agent" in text
        assert "developer_instructions" in text

    try:
        module.install_agents(tmp_path, dry_run=False)
    except FileExistsError as error:
        assert "context-manager.toml" in str(error)
    else:
        raise AssertionError("install_agents should reject existing files by default")


def test_install_skill_backup_preserves_existing_agent(tmp_path: Path) -> None:
    module = load_install_module()
    existing = tmp_path / ".codex" / "agents" / "context-manager.toml"
    existing.parent.mkdir(parents=True)
    existing.write_text("custom local agent\n", encoding="utf-8")

    targets = module.install_agents(tmp_path, dry_run=False, backup=True)

    backup = tmp_path / ".codex" / "agents" / "context-manager.toml.bak"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "custom local agent\n"
    assert existing.read_text(encoding="utf-8") != "custom local agent\n"
    assert targets[0] == existing


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


def test_shared_subagents_agents_block_documents_runtime_fallback() -> None:
    block = SHARED_SUBAGENTS_BLOCK.read_text(encoding="utf-8")

    assert "shared-subagents" in block
    assert "runtime does not expose subagents" in block


def test_shared_subagents_agents_block_defines_subagent_use_boundaries() -> None:
    block = SHARED_SUBAGENTS_BLOCK.read_text(encoding="utf-8")
    detailed_terms = (
        "Spec Ledger",
        "Spec-to-Plan Coverage Matrix",
        "Fixture Governance Contract",
        "validator evidence",
        "not-run items",
    )

    assert "<!-- SHARED-SUBAGENTS-START -->" in block
    assert "<!-- SHARED-SUBAGENTS-END -->" in block
    assert "routing shim" in block
    assert "references/superpowers-routing.md" in block
    assert "Spawn subagents only when the user explicitly asks" in block
    for agent_name in EXPECTED_AGENTS:
        assert f"`{agent_name}`" in block
    assert "Use `spec-coverage-reviewer`" in block
    assert "`completion-claim-reviewer`" in block
    assert "Use subagents for broad, parallelizable work" in block
    assert "Keep simple or single-file work in the main session" in block
    assert "reviewer/code-reviewer/security-auditor gates separate" in block
    assert block.count("\n- ") <= 6
    assert len(block.encode("utf-8")) <= 1500
    for term in detailed_terms:
        assert term not in block


def test_reviewer_defers_test_adequacy_and_plan_fidelity() -> None:
    instructions = agent_instructions("reviewer")

    assert "correctness risks and behavior regressions" in instructions
    assert "Security audit belongs to security-auditor" in instructions
    assert "security implications across input handling" not in instructions
    assert "Test adequacy belongs to test-adequacy-reviewer" in instructions
    assert "Requirement and plan fidelity belong to requirements-reviewer and plan-reviewer" in instructions
    assert "TDD review checks:" not in instructions
    assert "Return TDD review findings with:" not in instructions


def test_reviewer_limits_documentation_review_to_user_impacting_boundaries() -> None:
    instructions = agent_instructions("reviewer")

    assert "documentation omissions" in instructions
    assert "public API" in instructions
    assert "behavior boundary" in instructions
    assert "migration" in instructions
    assert "configuration" in instructions
    assert "user-visible" in instructions
    assert "Do not dilute findings with style-only commentary" in instructions


def test_shared_subagents_agents_block_keeps_review_gates_separate() -> None:
    block = SHARED_SUBAGENTS_BLOCK.read_text(encoding="utf-8")

    assert "reviewer/code-reviewer/security-auditor" in block
    assert "reviewer` and `code-reviewer`" not in block
