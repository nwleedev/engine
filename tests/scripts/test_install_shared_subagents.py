from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "shared-subagents"
    / "scripts"
    / "install_shared_subagents.py"
)

PLUGIN_ROOT = SCRIPT_PATH.parents[1]


def load_module():
    """Load the install script as a test module."""

    spec = importlib.util.spec_from_file_location("install_shared_subagents", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_returns_expected_targets(tmp_path: Path) -> None:
    module = load_module()

    targets = module.install_agents(tmp_path, dry_run=True)

    assert len(targets) == 8
    assert targets[0] == tmp_path / "agents" / "context-manager.toml"
    assert not (tmp_path / "agents").exists()


def test_install_copies_all_agents(tmp_path: Path) -> None:
    module = load_module()

    targets = module.install_agents(tmp_path, dry_run=False)

    assert len(targets) == 8
    for target in targets:
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "developer_instructions" in text


def test_plugin_manifest_exposes_scaffold_skill() -> None:
    manifest = (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(
        encoding="utf-8"
    )
    skill = PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md"

    assert '"name": "shared-subagents"' in manifest
    assert '"skills": "./skills/"' in manifest
    assert skill.exists()
    assert "name: scaffold" in skill.read_text(encoding="utf-8")


def test_scaffold_skill_references_shared_scripts() -> None:
    text = (
        PLUGIN_ROOT / "skills" / "scaffold" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "scripts/install_shared_subagents.py --dry-run" in text
    assert "scripts/print_agents_md_block.py" in text
    assert "Does not modify AGENTS.md automatically." in text
