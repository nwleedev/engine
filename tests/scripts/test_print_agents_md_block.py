from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "codex"
    / "shared-subagents"
    / "scripts"
    / "print_agents_md_block.py"
)


def load_module():
    """Load the print script as a test module."""

    spec = importlib.util.spec_from_file_location("print_agents_md_block", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_block_contains_markers() -> None:
    module = load_module()

    block = module.read_block()

    assert "<!-- SHARED-SUBAGENTS-START -->" in block
    assert "<!-- SHARED-SUBAGENTS-END -->" in block
    assert "context-manager" in block
    assert "online-researcher" in block
    assert "spec-reviewer" in block
