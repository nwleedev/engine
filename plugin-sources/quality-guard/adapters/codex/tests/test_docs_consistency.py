from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_readmes_share_skill_names_and_command():
    english = read("README.md")
    korean = read("README.ko.md")
    for token in (
        "quality-guard:retrospect",
        "quality-guard:install",
        "python3 /path/to/quality-guard/skills/install/install.py",
    ):
        assert token in english
        assert token in korean


def test_install_skill_uses_skill_relative_command():
    skill = (ROOT / "skills/install/SKILL.md").read_text(encoding="utf-8")

    assert "python3 /path/to/quality-guard/skills/install/install.py" in skill
    assert "python3 plugins/quality-guard/skills/install/install.py" not in skill


def test_readmes_share_output_schema():
    english = read("README.md")
    korean = read("README.ko.md")
    for token in (
        "Context status: complete | reconstructed | incomplete",
        "Superficial risk: none | low | medium | high | unknown",
        "optional session memory: used | unavailable | mismatch",
    ):
        assert token in english
        assert token in korean
