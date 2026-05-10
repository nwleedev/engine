from __future__ import annotations

from typing import Any


def render_claude_manifest(plugin: dict[str, Any]) -> dict[str, Any]:
    """Render canonical plugin metadata into a Claude plugin manifest."""

    return {
        "name": plugin["harnesses"]["claude"]["name"],
        "version": str(plugin["version"]),
        "description": plugin["description"],
        "license": plugin["license"],
    }


__all__ = ["render_claude_manifest"]
