from pathlib import Path


ROOT = Path("plugins/harness-foundry")
SKILLS = (
    "diagnose-project",
    "design-domain-harness",
    "update-registry",
    "scaffold-domain-harness",
    "audit-domain-harness",
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
