from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_readme_documents_generated_plugin_architecture() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "plugin-sources/",
        "plugins/codex/",
        "plugins/claude/",
        "python tools/build_plugins.py",
        "python tools/validate_generated.py",
        "git diff --exit-code",
    ):
        assert expected in readme


def test_readme_separates_current_state_from_migration_goal() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    korean_readme = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    for expected in (
        "plugin-sources/marketplace.yaml",
        "plugin-sources/shared-skills/",
        "source migration",
        "later tasks",
    ):
        assert expected in readme

    for expected in (
        "plugin-sources/marketplace.yaml",
        "plugin-sources/shared-skills/",
        "이후 작업",
    ):
        assert expected in korean_readme


def test_makefile_exposes_plugin_build_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "build-plugins:" in makefile
    assert "validate-generated:" in makefile
    assert "test-interop:" in makefile
    assert "test:" in makefile
    assert "test-interop" in makefile.split("test:", maxsplit=1)[1].splitlines()[0]
