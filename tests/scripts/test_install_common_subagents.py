from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "common-subagents"
    / "scripts"
    / "install_common_subagents.py"
)


def load_module():
    """Load the install script as a test module."""

    spec = importlib.util.spec_from_file_location("install_common_subagents", SCRIPT_PATH)
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
