from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_PLUGIN_PATHS = (
    "plugins/session-memory",
    "plugins/codex-session-memory",
    "plugins/quality-guard",
    "plugins/codex-quality-guard",
    "plugins/shared-skills",
    "plugins/shared-subagents",
    "plugins/harness-foundry",
)


def test_legacy_flat_plugin_paths_are_removed() -> None:
    for relative_path in LEGACY_PLUGIN_PATHS:
        assert not (ROOT / relative_path).exists(), relative_path
