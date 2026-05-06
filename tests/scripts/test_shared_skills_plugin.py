from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path("plugins/shared-skills")
SKILLS = (
    "requirements-clarifier",
    "research-crosscheck",
    "task-planner",
    "implementation-discipline",
    "debugging-discipline",
    "review-checklist",
    "verification-evidence",
)


def read(path: Path) -> str:
    """Read a UTF-8 text file from the repository."""

    return path.read_text(encoding="utf-8")


def test_manifest_exposes_shared_skills_plugin() -> None:
    manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

    manifest = json.loads(read(manifest_path))

    assert manifest["name"] == "shared-skills"
    assert manifest["version"] == "0.2.1"
    assert manifest["license"] == "MIT"
    assert manifest["skills"] == "./skills/"
    assert "main-session quality gates" in manifest["description"]


def test_all_lean_core_skills_exist_with_frontmatter() -> None:
    for skill_name in SKILLS:
        skill_path = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        text = read(skill_path)

        assert text.startswith("---\n")
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


def test_readme_documents_plugin_only_installation() -> None:
    readme = read(PLUGIN_ROOT / "README.md")

    assert "Plugin-only distribution" in readme
    assert "$shared-skills:" in readme
    assert "does not copy skills into" in readme
    assert "does not edit AGENTS.md" in readme


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
