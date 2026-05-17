from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LEGACY_PROMPT_ID = "research" "-prompt"


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_readme_documents_generated_plugin_architecture() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "plugin-sources/",
        "plugins/codex/",
        "plugins/claude/",
        "python tools/build_plugins.py",
        "python tools/validate_generated.py",
        "git diff --exit-code",
        "deep-research-prompt-export",
        "requirements-packet",
        "test-adequacy-reviewer",
        "docs/shared-skills/AGENTS.block.md",
        "docs/shared-subagents/AGENTS.block.md",
    ):
        assert expected in readme

    assert f"`{LEGACY_PROMPT_ID}`" not in readme


def test_readme_separates_current_state_from_migration_goal() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    korean_readme = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    compact_readme = _compact(readme)
    compact_korean_readme = _compact(korean_readme)

    for expected in (
        "plugin-sources/marketplace.yaml",
        "renders full plugin trees from `plugin-sources/`",
        "`session-memory`, `quality-guard`, `shared-skills`, `shared-subagents`, and `harness-foundry`",
        "`_packages/` directory",
        "`deep-research-prompt-export`",
        "`requirements-packet`",
        "`test-adequacy-reviewer`",
    ):
        assert expected in compact_readme

    for expected in (
        "plugin-sources/marketplace.yaml",
        "`plugin-sources/`",
        "`session-memory`, `quality-guard`, `shared-skills`, `shared-subagents`, `harness-foundry`",
        "`_packages/`",
        "`deep-research-prompt-export`",
        "`requirements-packet`",
        "`test-adequacy-reviewer`",
    ):
        assert expected in compact_korean_readme

    assert f"`{LEGACY_PROMPT_ID}`" not in korean_readme


def test_makefile_exposes_plugin_build_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "build-plugins:" in makefile
    assert "validate-generated:" in makefile
    assert "test-interop:" in makefile
    assert "test:" in makefile
    assert "test-interop" in makefile.split("test:", maxsplit=1)[1].splitlines()[0]
