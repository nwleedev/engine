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
    "domain-harness-eval-metrics.md",
    "improvement-report-template.md",
    "sanitized-regression-case-template.md",
    "downstream-issue-template.md",
    "downstream-adoption-guide.md",
)
ISSUE_TEMPLATE_FILES = (
    "harness-quality-issue.yml",
    "upstream-regression-case.yml",
    "harness-feature-request.yml",
    "config.yml",
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


def test_issue_template_assets_are_complete():
    template_dir = ROOT / "assets" / "github-templates" / "ISSUE_TEMPLATE"
    for template_file in ISSUE_TEMPLATE_FILES:
        assert (template_dir / template_file).is_file()
    assert (ROOT / "assets" / "github-templates" / "pull_request_template.md").is_file()


def test_issue_templates_include_privacy_sanitization_check():
    for template_file in ISSUE_TEMPLATE_FILES[:3]:
        text = read(f"assets/github-templates/ISSUE_TEMPLATE/{template_file}")
        assert "privacy_sanitization_check" in text


def test_improvement_report_template_has_required_sections():
    text = read("references/improvement-report-template.md")
    for heading in (
        "## Summary",
        "## Affected harnesses",
        "## Findings",
        "## Local fix candidates",
        "## Upstream regression candidates",
        "## Privacy and sanitization review",
        "## Verification checklist",
        "## Open questions",
    ):
        assert heading in text


def test_downstream_adoption_guide_defines_operator_run_boundary():
    text = read("references/downstream-adoption-guide.md")
    for phrase in (
        "Operator-run is the default v1 adoption model.",
        "docs/domain-harness/reports/<date>-improvement-report.md",
        "GitHub issue and PR templates remain passive assets until explicit approval.",
        "Do not copy downstream project source, customer data, internal documents, or credentials into upstream fixtures.",
        "Separate local fixes from upstream regression candidates.",
    ):
        assert phrase in text


def test_readmes_explain_downstream_adoption_models():
    english = read("README.md")
    korean = read("README.ko.md")
    for phrase in (
        "Operator-run",
        "Project-local tooling",
        "Plugin-mediated workflow",
    ):
        assert phrase in english
    assert "Operator-run" in korean
    assert "현업 프로젝트의 report는 자동 저장하지 않습니다" in korean


def test_scaffold_skill_requires_downstream_approval_gates():
    text = read("skills/scaffold-domain-harness/SKILL.md")
    for phrase in (
        "Phase 0",
        "docs/domain-harness/** files require explicit approval",
        "diff preview",
        "rollback note",
        "Phase 7",
    ):
        assert phrase in text


def test_audit_skill_classifies_downstream_findings():
    text = read("skills/audit-domain-harness/SKILL.md")
    for phrase in (
        "validate_domain_harness.py",
        "local harness issue",
        "upstream plugin issue",
        "runtime activation issue",
        "privacy_sanitization_check",
    ):
        assert phrase in text
