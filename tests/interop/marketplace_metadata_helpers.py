from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

METADATA = ROOT / "plugin-sources" / "marketplace.yaml"
CODEX_MANIFESTS_BY_PUBLIC_NAME = {
    "session-memory": ROOT
    / "plugins"
    / "codex"
    / "session-memory"
    / ".codex-plugin"
    / "plugin.json",
    "quality-guard": ROOT
    / "plugins"
    / "codex"
    / "quality-guard"
    / ".codex-plugin"
    / "plugin.json",
    "shared-subagents": ROOT
    / "plugins"
    / "codex"
    / "shared-subagents"
    / ".codex-plugin"
    / "plugin.json",
    "shared-skills": ROOT
    / "plugins"
    / "codex"
    / "shared-skills"
    / ".codex-plugin"
    / "plugin.json",
    "harness-foundry": ROOT
    / "plugins"
    / "codex"
    / "harness-foundry"
    / ".codex-plugin"
    / "plugin.json",
    "deep-research-prompt-export": ROOT
    / "plugins"
    / "codex"
    / "deep-research-prompt-export"
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
    "deep-research-prompt-export": {
        "claude": "./plugins/claude/deep-research-prompt-export",
        "codex": "./plugins/codex/deep-research-prompt-export",
    },
}
EXPECTED_HARNESS_PUBLIC_NAMES = {
    "session-memory": {"claude": "session-memory", "codex": "session-memory"},
    "quality-guard": {"claude": "quality-guard", "codex": "quality-guard"},
    "shared-subagents": {"claude": "shared-subagents", "codex": "shared-subagents"},
    "shared-skills": {"claude": "shared-skills", "codex": "shared-skills"},
    "harness-foundry": {"claude": "harness-foundry", "codex": "harness-foundry"},
    "deep-research-prompt-export": {
        "claude": "deep-research-prompt-export",
        "codex": "deep-research-prompt-export",
    },
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
                "version": "0.5.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "session-memory",
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
        "    version: 0.5.0",
        "    description: Automatic session context narration and injection",
        "    license: MIT",
        "    category: Productivity",
        "    harnesses:",
        "      codex:",
        "        name: session-memory",
        "        path: ./plugins/codex/session-memory",
    ]
