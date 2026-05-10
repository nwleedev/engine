from pathlib import Path


ROOT = Path("plugins/codex/quality-guard")


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_readmes_share_skill_names_and_command():
    english = read("README.md")
    korean = read("README.ko.md")
    for token in (
        "codex-quality-guard:retrospect",
        "codex-quality-guard:install",
        "python3 /path/to/codex-quality-guard/skills/install/install.py",
    ):
        assert token in english
        assert token in korean


def test_install_skill_uses_skill_relative_command():
    skill = Path("plugins/codex/quality-guard/skills/install/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "python3 /path/to/codex-quality-guard/skills/install/install.py" in skill
    assert "python3 plugins/" not in skill


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
