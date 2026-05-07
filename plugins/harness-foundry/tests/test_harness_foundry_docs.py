from pathlib import Path


ROOT = Path("plugins/harness-foundry")
SKILLS = (
    "diagnose-project",
    "design-domain-harness",
    "update-registry",
    "scaffold-domain-harness",
    "audit-domain-harness",
)
REFERENCE_FILES = (
    "domain-harness-template.md",
    "registry-template.md",
    "evaluation-template.md",
    "risk-checklist.md",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readmes_list_all_skills():
    english = read("README.md")
    korean = read("README.ko.md")
    for skill in SKILLS:
        assert skill in english
        assert skill in korean


def test_skills_keep_v1_boundaries():
    combined = "\n".join(read(f"skills/{skill}/SKILL.md") for skill in SKILLS)
    assert "Do not recommend bulk-installing public awesome repositories." in combined
    assert (
        "AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval"
        in combined
    )
    assert "index.json" in read("skills/update-registry/SKILL.md")


def test_korean_readme_is_supplementary():
    korean = read("README.ko.md")
    assert "영어 README와 `SKILL.md`가 canonical 문서" in korean
    assert "한국어 사용자를 위한 보조 설명" in korean


def test_required_references_exist():
    for reference_file in REFERENCE_FILES:
        assert (ROOT / "references" / reference_file).is_file()


def test_readmes_do_not_expose_downstream_loop():
    combined = read("README.md") + "\n" + read("README.ko.md")
    for phrase in (
        "Downstream " + "Quality Loop",
        "Downstream " + "Adoption Models",
        "Operator-" + "run",
        "Project-local " + "tooling",
        "Plugin-mediated " + "workflow",
        "privacy_" + "sanitization_check",
    ):
        assert phrase not in combined


def test_scaffold_skill_requires_downstream_approval_gates():
    text = read("skills/scaffold-domain-harness/SKILL.md")
    for phrase in (
        "Phase 0",
        "docs/domain-harness/** files require explicit approval",
        "diff preview",
        "rollback note",
        "GitHub issue and PR templates are outside the v1 public plugin scaffold flow.",
    ):
        assert phrase in text


def test_audit_skill_stays_in_public_plugin_scope():
    text = read("skills/audit-domain-harness/SKILL.md")
    assert "Perform a read-only audit" in text
    assert "Findings ordered by severity" in text
    for phrase in (
        "downstream",
        "upstream " + "plugin issue",
        "privacy_" + "sanitization_check",
        "validate_" + "domain_harness.py",
    ):
        assert phrase not in text
