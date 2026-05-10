from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path("plugins/codex/shared-skills")
SKILLS = (
    "requirements-clarifier",
    "research-crosscheck",
    "task-planner",
    "implementation-discipline",
    "debugging-discipline",
    "review-checklist",
    "verification-evidence",
    "tdd-test-writing",
    "comment-spec-writing",
)


def read(path: Path) -> str:
    """Read a UTF-8 text file from the repository."""

    return path.read_text(encoding="utf-8")


def section_body(text: str, heading: str) -> str:
    """Return the body until the next Markdown level-two heading line."""

    lines = text.splitlines()
    start_heading = f"## {heading}"
    start_index = lines.index(start_heading) + 1
    end_index = len(lines)

    for index in range(start_index, len(lines)):
        if lines[index].startswith("## "):
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def test_manifest_exposes_shared_skills_plugin() -> None:
    manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

    manifest = json.loads(read(manifest_path))

    assert manifest["name"] == "shared-skills"
    assert manifest["version"] == "0.2.4"
    assert manifest["license"] == "MIT"
    assert manifest["skills"] == "./skills/"
    assert "main-session quality gates" in manifest["description"]


def test_all_lean_core_skills_exist_with_frontmatter() -> None:
    for skill_name in SKILLS:
        skill_path = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        text = read(skill_path)
        source_path = f"plugin-sources/shared-skills/skills/{skill_name}/SKILL.md"

        assert text.startswith("<!-- GENERATED FILE - DO NOT EDIT -->\n")
        assert f"<!-- source: {source_path} -->\n\n---\n" in text
        assert f"name: {skill_name}" in text
        assert "description: Use when" in text
        assert "metadata:\n  short-description:" in text
        assert "\n---\n" in text


def test_skills_cover_development_and_non_development_work() -> None:
    for skill_name in SKILLS:
        text = read(PLUGIN_ROOT / "skills" / skill_name / "SKILL.md")

        assert "Workflow" in text
        assert "Development work" in text
        assert "Non-development work" in text
        assert "Output" in text
        assert "Do not" in text


def test_requirements_clarifier_handles_many_ambiguities() -> None:
    text = read(PLUGIN_ROOT / "skills" / "requirements-clarifier" / "SKILL.md")

    assert "Identify all ambiguities first." in text
    assert "Ask only the highest-priority blocking question per assistant turn." in text
    assert "Do not hide other ambiguities." in text


def test_research_crosscheck_requires_counterevidence() -> None:
    text = read(PLUGIN_ROOT / "skills" / "research-crosscheck" / "SKILL.md")

    assert "Prefer official or primary sources." in text
    assert "MCP server specialized for up-to-date library and framework documentation" in text
    assert "MCP server specialized for external source discovery" in text
    assert "Counterevidence" in text


def test_review_and_verification_have_separate_responsibilities() -> None:
    review = read(PLUGIN_ROOT / "skills" / "review-checklist" / "SKILL.md")
    verification = read(PLUGIN_ROOT / "skills" / "verification-evidence" / "SKILL.md")

    assert "Review finds defects, gaps, and risks." in review
    assert "Verification gathers evidence for claims." in verification
    assert "Do not claim completion from review alone." in review
    assert "Do not claim completion without fresh evidence." in verification


def test_tdd_test_writing_skill_defines_tdd_workflow() -> None:
    text = read(PLUGIN_ROOT / "skills" / "tdd-test-writing" / "SKILL.md")

    assert "Purpose" in text
    assert "When to use" in text
    assert "Inputs to inspect" in text
    assert "Workflow" in text
    assert "Test type decision matrix" in text
    assert "Test writing rules" in text
    assert "Stack detection rules" in text
    assert "Review handoff" in text
    assert "Output" in text
    assert "Do not" in text
    assert "TDD" in text
    assert "failing test" in text
    assert "detected stack" in text
    assert "flaky" in text
    assert "Arrange-Act-Assert" in text
    assert "reviewer handoff" in text


def test_comment_spec_writing_skill_defines_comment_workflow() -> None:
    text = read(PLUGIN_ROOT / "skills" / "comment-spec-writing" / "SKILL.md")

    assert "Purpose" in text
    assert "When to use" in text
    assert "Inputs to inspect" in text
    assert "Workflow" in text
    assert "Documentation target decision matrix" in text
    assert "Stack-specific comment formats" in text
    assert "Comment quality rules" in text
    assert "Review handoff" in text
    assert "Output" in text
    assert "Do not" in text
    assert "public/exported" in text
    assert "Explain why, not just what." in text
    assert "Do not repeat" in text
    assert "Javadoc" in text
    assert "KDoc" in text
    assert "JSDoc" in text
    assert "docstring" in text
    assert "rustdoc" in text
    assert "docs-researcher handoff" in text
    assert "code-reviewer handoff" in text
    assert "clearer code before comments" in text


def test_comment_specs_reference_documents_required_stacks() -> None:
    text = read(PLUGIN_ROOT / "references" / "comment-specs-by-stack.md")
    first_heading = next(line for line in text.splitlines() if line.startswith("# "))

    assert first_heading == "# Comment Specs by Stack"
    assert "## Code clarity before comments" in text
    assert "## Stack-specific formats" in text
    assert "## Review questions" in text
    assert "| Stack | Preferred format | Applies to | Notes | Official source |" in text
    assert "Code clarity before comments" in text
    assert "Javadoc" in text
    assert "KDoc" in text
    assert "JSDoc" in text
    assert "TSDoc" in text
    assert "docstring" in text
    assert "PEP 257" in text
    assert "Go doc comments" in text
    assert "rustdoc" in text
    assert "XML documentation comments" in text
    assert "PHPDoc" in text
    assert "RDoc" in text
    assert "YARD" in text
    assert "Swift" in text
    assert "Objective-C" in text
    assert "Doxygen" in text
    assert "COMMENT ON" in text
    assert "Shell" in text
    assert "Terraform" in text
    assert "Dockerfile" in text
    assert "Kubernetes" in text
    assert "OpenAPI" in text
    assert "GraphQL" in text
    assert "Proto" in text
    assert "official source" in text
    assert "unrelated refactoring" in text


def test_tdd_test_types_reference_documents_required_types() -> None:
    text = read(PLUGIN_ROOT / "references" / "tdd-test-types.md")
    test_types = (
        "Unit",
        "Integration",
        "Contract",
        "Component",
        "End-to-end",
        "Smoke",
        "Regression",
        "Characterization",
        "Property-based",
        "Snapshot/Golden",
        "Performance/Benchmark",
        "Security",
        "Accessibility",
        "Migration/Schema",
        "Infrastructure/IaC validation",
    )
    required_labels = (
        "- **When to use:**",
        "- **What to verify:**",
        "- **What to avoid:**",
        "- **Test code structure:**",
        "- **Assertion standard:**",
        "- **Fixture, mock, stub, fake use:**",
        "- **Flaky test prevention:**",
        "- **TDD first failing test:**",
        "- **Use existing project tools first:**",
    )

    assert "# TDD Test Types" in text
    double_priority = section_body(text, "Test double priority")
    assert "inline minimal arrange" in double_priority
    assert "real domain objects" in double_priority
    assert "repeated arrange becomes clearer with a name" in double_priority
    assert "unused setup does not hide test intent" in double_priority
    assert "Use a mock only when the outbound interaction contract itself is the requirement" in double_priority

    lines = text.splitlines()
    previous_heading_index = -1
    for test_type in test_types:
        heading_index = lines.index(f"## {test_type}")
        assert heading_index > previous_heading_index
        previous_heading_index = heading_index

        section = section_body(text, test_type)

        previous_position = -1
        for label in required_labels:
            position = section.find(label)
            assert position > previous_position
            next_positions = [
                section.find(next_label, position + len(label))
                for next_label in required_labels
                if section.find(next_label, position + len(label)) != -1
            ]
            end_position = min(next_positions) if next_positions else len(section)
            assert section[position + len(label) : end_position].strip()
            previous_position = position

    assert "When to use" in text
    assert "What to verify" in text
    assert "What to avoid" in text
    assert "TDD first failing test" in text


def test_readme_documents_plugin_only_installation() -> None:
    readme = read(Path("plugins/shared-skills/README.md"))

    assert "Plugin-only distribution" in readme
    assert "$shared-skills:" in readme
    assert "- `tdd-test-writing`:" in readme
    assert "- `comment-spec-writing`:" in readme
    assert "does not copy skills into" in readme
    assert "does not edit AGENTS.md" in readme


def test_implementation_discipline_prefers_clear_code_before_comments() -> None:
    text = read(PLUGIN_ROOT / "skills" / "implementation-discipline" / "SKILL.md")

    assert "Before explaining unclear code with comments" in text
    assert "better names" in text
    assert "named constants" in text
    assert "extracted expressions/functions" in text
    assert "typed options" in text
    assert "approved scope" in text
    assert "Do not turn readability cleanup into unrelated refactoring" in text


def test_no_scaffold_or_copy_install_flow_exists() -> None:
    assert not (PLUGIN_ROOT / "skills" / "scaffold").exists()
    assert not (PLUGIN_ROOT / "scripts").exists()

    combined = "\n".join(
        read(path)
        for path in sorted(PLUGIN_ROOT.rglob("*"))
        if path.is_file() and path.suffix in {".md", ".json"}
    )

    assert "--install --backup" not in combined
    assert "$CODEX_HOME/skills" not in combined
    assert "~/.codex/skills" not in combined
