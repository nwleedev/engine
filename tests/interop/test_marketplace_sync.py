from __future__ import annotations

import sys
from pathlib import Path

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from marketplace_metadata_helpers import METADATA
from renderers.claude.marketplaces import render_claude_marketplace
from renderers.codex.marketplaces import render_codex_marketplace
from tools.build.metadata import load_marketplace


def test_render_codex_marketplace_maps_session_memory_plugin() -> None:
    metadata = load_marketplace(METADATA)

    marketplace = render_codex_marketplace(metadata)
    session_memory = next(
        plugin for plugin in marketplace["plugins"] if plugin["name"] == "session-memory"
    )

    assert marketplace["name"] == "engine"
    assert marketplace["interface"] == {"displayName": "Utils with session continuity"}
    assert session_memory == {
        "name": "session-memory",
        "source": {"source": "local", "path": "./plugins/codex/session-memory"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }


def test_render_claude_marketplace_maps_session_memory_plugin() -> None:
    metadata = load_marketplace(METADATA)

    marketplace = render_claude_marketplace(metadata)
    session_memory = next(
        plugin for plugin in marketplace["plugins"] if plugin["name"] == "session-memory"
    )

    assert marketplace["$schema"] == "https://anthropic.com/claude-code/marketplace.schema.json"
    assert marketplace["name"] == "engine"
    assert marketplace["description"] == (
        "Claude Code Harness System — plan enforcement, quality gates, "
        "domain knowledge, and session continuity"
    )
    assert marketplace["owner"] == {"name": "nwleedev"}
    assert session_memory == {
        "name": "session-memory",
        "description": "Automatic session context narration and injection",
        "source": "./plugins/claude/session-memory",
    }


def test_render_claude_marketplace_copies_owner_metadata() -> None:
    metadata = load_marketplace(METADATA)

    marketplace = render_claude_marketplace(metadata)
    marketplace["owner"]["name"] = "changed-owner"

    assert metadata["owner"] == {"name": "nwleedev"}


def test_render_codex_marketplace_includes_all_codex_plugins() -> None:
    metadata = load_marketplace(METADATA)

    marketplace = render_codex_marketplace(metadata)

    assert [plugin["name"] for plugin in marketplace["plugins"]] == [
        "session-memory",
        "quality-guard",
        "shared-subagents",
        "shared-skills",
        "harness-foundry",
        "research-prompt",
    ]


def test_render_claude_marketplace_includes_all_claude_plugins() -> None:
    metadata = load_marketplace(METADATA)

    marketplace = render_claude_marketplace(metadata)

    assert [plugin["name"] for plugin in marketplace["plugins"]] == [
        "session-memory",
        "quality-guard",
        "shared-subagents",
        "shared-skills",
        "harness-foundry",
        "research-prompt",
    ]
