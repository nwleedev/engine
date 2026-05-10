from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
# pytest importlib mode does not add the project root for this interop import.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers import plugin_tree
from tools.build.headers import markdown_header, python_header

CODEX_ARTIFACT = ROOT / "plugins" / "codex" / "harness-foundry"
CLAUDE_ARTIFACT = ROOT / "plugins" / "claude" / "harness-foundry"
SOURCE = ROOT / "plugin-sources" / "harness-foundry"
VALIDATOR_COMMAND_PATTERN = re.compile(
    r"rtk python3 (?P<path>\S*validate_domain_harness\.py) <project-root>"
)


def _read_json(path: Path) -> dict[str, object]:
    """Read a generated JSON manifest from a plugin artifact."""

    return json.loads(path.read_text(encoding="utf-8"))


def _assert_artifact_includes_generated_tree(target: Path, harness: str) -> None:
    """Assert that a harness-foundry artifact includes rendered source files."""

    manifest_path = (
        ".codex-plugin/plugin.json"
        if harness == "codex"
        else ".claude-plugin/plugin.json"
    )
    skill_path = target / "skills" / "design-domain-harness" / "SKILL.md"
    helper_path = (
        target
        / "skills"
        / "audit-domain-harness"
        / "scripts"
        / "validate_domain_harness.py"
    )

    assert skill_path.exists()
    assert skill_path.read_text(encoding="utf-8").startswith(
        markdown_header(
            "plugin-sources/harness-foundry/skills/design-domain-harness/SKILL.md"
        )
    )
    assert helper_path.exists()
    assert helper_path.read_text(encoding="utf-8").startswith(
        python_header(
            "plugin-sources/harness-foundry/skills/audit-domain-harness/scripts/"
            "validate_domain_harness.py"
        )
    )
    assert (target / "README.md").read_text(encoding="utf-8").startswith(
        markdown_header("plugin-sources/harness-foundry/README.md")
    )
    assert (target / "README.ko.md").read_text(encoding="utf-8").startswith(
        markdown_header("plugin-sources/harness-foundry/README.ko.md")
    )
    assert (target / "references" / "registry-template.md").read_text(
        encoding="utf-8"
    ).startswith(
        markdown_header(
            "plugin-sources/harness-foundry/references/registry-template.md"
        )
    )
    assert not (target / "hooks").exists(), f"{harness} artifact must not include hooks"
    assert not (target / "scripts" / "mutate_agents.py").exists()
    assert not (target / "background-monitor").exists()
    assert not (target / "AGENTS.md").exists()
    artifact_files = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    }
    source_files = {
        source_path.relative_to(SOURCE).as_posix()
        for source_path in SOURCE.rglob("*")
        if _is_rendered_source_file(source_path)
    }
    assert artifact_files == {*source_files, manifest_path, ".generated.json"}


def _extract_validator_command_path(readme_path: Path) -> str:
    """Return the validator script path from a generated plugin README."""

    text = readme_path.read_text(encoding="utf-8")
    match = VALIDATOR_COMMAND_PATTERN.search(text)
    assert match is not None
    return match.group("path")


def _is_rendered_source_file(path: Path) -> bool:
    """Return whether a source file is allowed in generated artifacts."""

    if not path.is_file():
        return False
    if path.suffix == ".md":
        return True
    return (
        path.suffix == ".py"
        and path.parent.name == "scripts"
        and "skills" in path.relative_to(SOURCE).parts
    )


def test_codex_harness_foundry_artifact_is_rendered() -> None:
    manifest = _read_json(CODEX_ARTIFACT / ".codex-plugin" / "plugin.json")

    assert manifest["name"] == "harness-foundry"
    _assert_artifact_includes_generated_tree(CODEX_ARTIFACT, "codex")


def test_claude_harness_foundry_artifact_is_rendered() -> None:
    manifest = _read_json(CLAUDE_ARTIFACT / ".claude-plugin" / "plugin.json")

    assert manifest["name"] == "harness-foundry"
    _assert_artifact_includes_generated_tree(CLAUDE_ARTIFACT, "claude")


def test_renderer_rejects_unsupported_source_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(plugin_tree, "ROOT", tmp_path)
    source_root = tmp_path / "harness-foundry"
    unsupported_file = source_root / "skills" / "example" / "data.json"
    unsupported_file.parent.mkdir(parents=True)
    unsupported_file.write_text("{}", encoding="utf-8")
    (source_root / "README.md").write_text("# test\n", encoding="utf-8")
    (source_root / "README.ko.md").write_text("# test\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported plugin source file"):
        plugin_tree.render_plugin_text_tree(source_root)


@pytest.mark.parametrize("target", [CODEX_ARTIFACT, CLAUDE_ARTIFACT])
@pytest.mark.parametrize("readme_name", ["README.md", "README.ko.md"])
def test_generated_readme_validator_command_is_artifact_internal(
    target: Path, readme_name: str
) -> None:
    command_path = _extract_validator_command_path(target / readme_name)

    assert "plugins/harness-foundry" not in command_path
    assert (
        command_path
        == "skills/audit-domain-harness/scripts/validate_domain_harness.py"
    )
    assert (target / command_path).is_file()
