from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

METADATA = ROOT / "plugin-sources" / "marketplace.yaml"
CODEX_MANIFESTS_BY_PUBLIC_NAME = {
    "codex-session-memory": ROOT
    / "plugins"
    / "codex-session-memory"
    / ".codex-plugin"
    / "plugin.json",
    "codex-quality-guard": ROOT
    / "plugins"
    / "codex-quality-guard"
    / ".codex-plugin"
    / "plugin.json",
    "shared-subagents": ROOT
    / "plugins"
    / "shared-subagents"
    / ".codex-plugin"
    / "plugin.json",
    "shared-skills": ROOT
    / "plugins"
    / "shared-skills"
    / ".codex-plugin"
    / "plugin.json",
    "harness-foundry": ROOT
    / "plugins"
    / "harness-foundry"
    / ".codex-plugin"
    / "plugin.json",
}
PLANNED_HARNESS_PATHS = {
    "session-memory": {
        "claude": "./plugins/claude/session-memory",
        "codex": "./plugins/codex/session-memory",
    },
    "quality-guard": {
        "claude": "./plugins/claude/quality-guard",
        "codex": "./plugins/codex/quality-guard",
    },
    "shared-subagents": {
        "claude": "./plugins/claude/shared-subagents",
        "codex": "./plugins/codex/shared-subagents",
    },
    "shared-skills": {
        "claude": "./plugins/claude/shared-skills",
        "codex": "./plugins/codex/shared-skills",
    },
    "harness-foundry": {
        "claude": "./plugins/claude/harness-foundry",
        "codex": "./plugins/codex/harness-foundry",
    },
}
EXPECTED_HARNESS_PUBLIC_NAMES = {
    "session-memory": {"claude": "session-memory", "codex": "codex-session-memory"},
    "quality-guard": {"claude": "quality-guard", "codex": "codex-quality-guard"},
    "shared-subagents": {"claude": "shared-subagents", "codex": "shared-subagents"},
    "shared-skills": {"claude": "shared-skills", "codex": "shared-skills"},
    "harness-foundry": {"claude": "harness-foundry", "codex": "harness-foundry"},
}


def minimal_marketplace_metadata() -> dict[Any, Any]:
    """Return the smallest valid marketplace metadata shape used by tests."""

    return {
        "name": "engine",
        "display_name": "Engine",
        "description": "Minimal metadata",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            }
        ],
    }


def write_metadata(path: Path, lines: list[str]) -> Path:
    """Write a marketplace YAML test fixture and return its path."""

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def minimal_marketplace_lines() -> list[str]:
    """Return a minimal valid YAML fixture for parser and loader tests."""

    return [
        "name: engine",
        "display_name: Engine",
        "description: Minimal metadata",
        "owner:",
        "  name: nwleedev",
        "plugins:",
        "  - id: session-memory",
        "    version: 0.4.0",
        "    description: Automatic session context narration and injection",
        "    license: MIT",
        "    category: Productivity",
        "    harnesses:",
        "      codex:",
        "        name: codex-session-memory",
        "        path: ./plugins/codex/session-memory",
    ]
