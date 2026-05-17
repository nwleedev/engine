from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEARNABLE = ROOT / "plugin-sources" / "learnable"
ADAPTER_README = LEARNABLE / "adapters" / "codex" / "README.md"
SKILLS = LEARNABLE / "adapters" / "codex" / "skills"
REFERENCES = LEARNABLE / "references"
README = LEARNABLE / "README.md"

EXPECTED_SKILLS = {
    "entry",
    "map-project",
    "check-docs",
    "write-material",
    "organize-materials",
    "verify-material",
    "serve-materials",
}

EXPECTED_REFERENCES = {
    "material-schema.md",
    "session-model.md",
    "policy.md",
    "entry-routing.md",
    "source-policy.md",
    "role-prompts.md",
    "security-review.md",
    "server-workflow.md",
}

REQUIRED_REFERENCES = EXPECTED_REFERENCES


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def _markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def test_learnable_skill_directory_matches_mvp_contract() -> None:
    assert {path.name for path in SKILLS.iterdir() if path.is_dir()} == EXPECTED_SKILLS
    assert not (SKILLS / "learnable" / "SKILL.md").exists()


def test_learnable_skills_have_required_frontmatter_and_valid_links() -> None:
    for skill in EXPECTED_SKILLS:
        skill_path = SKILLS / skill / "SKILL.md"
        text = _text(skill_path)
        frontmatter = _frontmatter(text)

        assert frontmatter["name"] == skill
        assert frontmatter["description"].startswith("Use when")
        for link in _markdown_links(text):
            if link.startswith(("http://", "https://", "#")):
                continue
            assert (skill_path.parent / link).resolve().exists(), f"{skill}: {link}"


def test_learnable_reference_files_exist() -> None:
    assert REQUIRED_REFERENCES <= {path.name for path in REFERENCES.glob("*.md")}
    assert ADAPTER_README.is_file()


def test_learnable_readmes_use_valid_relative_links() -> None:
    for path in [README, ADAPTER_README]:
        for link in _markdown_links(_text(path)):
            if link.startswith(("http://", "https://", "#")):
                continue
            assert (path.parent / link).resolve().exists(), f"{path.name}: {link}"


def test_entry_skill_stays_compact_and_delegates_routing_matrix() -> None:
    entry = _text(SKILLS / "entry" / "SKILL.md")

    assert len(entry.splitlines()) < 500
    for link in [
        "../../../../references/entry-routing.md",
        "../../../../references/policy.md",
        "../../../../references/role-prompts.md",
    ]:
        assert link in entry
    for token in [
        "prompt",
        "project_dir",
        "target_path",
        "target_symbol",
        "learnable_session_id",
        "parent_node_id",
        "audience_level",
        "output_mode",
        "source_policy",
    ]:
        assert token in entry
    assert "이 함수" in entry
    assert "answer-only" in entry
    assert "outline" in entry
    assert "Shared plugins are optional" in entry
    assert "session-memory checkpoint boundaries" in entry


def test_entry_routing_reference_defines_input_contract_modes_and_no_mutation_policy() -> None:
    routing = _text(REFERENCES / "entry-routing.md")

    for phrase in [
        "`project_dir`: defaults to the current project root",
        "`target_path`: repository-relative file or directory",
        "`target_symbol`: function, class, method, command, config key, or UI element",
        "`learnable_session_id`: existing Learnable material session id",
        "`parent_node_id`: existing material node id",
        "`output_mode`: defaults to `material`",
        "`source_policy`: one of `local-only`, `official-docs`, or `web-allowed`",
    ]:
        assert phrase in routing
    for value in ["beginner", "maintainer", "operator", "auto"]:
        assert value in routing
    for value in ["material", "answer-only", "outline", "serve"]:
        assert value in routing
    assert "answer-only" in routing and "must not mutate `.codex/materials`" in routing
    assert "outline" in routing and "must not mutate `.codex/materials`" in routing


def test_subskills_link_to_required_references_and_policy() -> None:
    required_links = {
        "check-docs": ["../../../../references/source-policy.md"],
        "write-material": ["../../../../references/material-schema.md"],
        "organize-materials": ["../../../../references/session-model.md"],
        "verify-material": [
            "../../../../references/source-policy.md",
            "../../../../references/security-review.md",
        ],
        "serve-materials": ["../../../../references/server-workflow.md"],
    }
    for skill, links in required_links.items():
        text = _text(SKILLS / skill / "SKILL.md")
        for link in links:
            assert link in text
    for skill in EXPECTED_SKILLS:
        text = _text(SKILLS / skill / "SKILL.md")
        assert "../../../../references/policy.md" in text
        assert "Shared plugins are optional" in text


def test_policy_is_canonical_for_session_memory_and_shared_plugin_boundaries() -> None:
    policy = _text(REFERENCES / "policy.md")

    for phrase in [
        ".codex/materials",
        "$session-memory:checkpoint",
        "unless the user explicitly asks",
        ".codex/session-memory",
        "shared-skills/shared-subagents",
        "Learnable must work without them",
    ]:
        assert phrase in policy


def test_source_policy_and_security_review_contracts() -> None:
    source_policy = _text(REFERENCES / "source-policy.md")
    security = _text(REFERENCES / "security-review.md")
    verify = _text(SKILLS / "verify-material" / "SKILL.md")

    for value in ["local-only", "official-docs", "web-allowed"]:
        assert value in source_policy
    for value in [
        "sensitive data",
        "path boundary",
        "prompt leakage",
        "token leakage",
        "private material paths",
        "unsafe source excerpts",
    ]:
        assert value in security
    assert "references/security-review.md" in verify
    assert len(verify.splitlines()) < 180


def test_role_prompts_define_learnable_owned_fallbacks() -> None:
    roles = _text(REFERENCES / "role-prompts.md")
    routing = _text(REFERENCES / "entry-routing.md")

    for mapping in [
        "project-mapper -> optional code-mapper",
        "docs-verifier -> optional docs-researcher",
        "material-writer -> main-session fallback",
        "material-curator -> main-session fallback",
        "accuracy-reviewer -> optional citation-verifier or reviewer",
        "security-reviewer -> optional security-auditor",
    ]:
        assert mapping in roles
        assert mapping.split(" -> ")[0] in routing
    assert "If optional shared plugins are unavailable, Learnable performs the same checks in the main session." in roles


def test_readme_exposes_optional_compact_agents_block_without_project_docs_dependency() -> None:
    readme = _text(README)

    assert "<!-- LEARNABLE-WORKFLOW-START -->" in readme
    assert "<!-- LEARNABLE-WORKFLOW-END -->" in readme
    assert "## Learnable Workflow" in readme
    assert "Use `$learnable:entry`" in readme
    assert "Use `learnable:entry`" in readme
    assert "Detailed policy lives in the installed Learnable plugin README/references" in readme
    assert "do not require project-local `docs/learnable/*`" in readme
    assert "If this block is missing, Learnable still works in MVP" in readme
    assert "Re-review this block before adding browser prompt UI or automated workers." in readme
    assert "Do not follow Learnable workflow instructions when the Learnable plugin is not installed" in readme
    assert not (ROOT / "docs" / "learnable").exists()

    block = readme.split("<!-- LEARNABLE-WORKFLOW-START -->", 1)[1].split(
        "<!-- LEARNABLE-WORKFLOW-END -->", 1
    )[0]
    bullets = [line for line in block.splitlines() if line.startswith("- ")]
    assert 3 <= len(bullets) <= 6
