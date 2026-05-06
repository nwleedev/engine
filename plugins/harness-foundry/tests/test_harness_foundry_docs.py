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
