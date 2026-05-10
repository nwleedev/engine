from __future__ import annotations

from typing import Any

CLAUDE_MARKETPLACE_SCHEMA = "https://anthropic.com/claude-code/marketplace.schema.json"


def render_claude_marketplace(metadata: dict[str, Any]) -> dict[str, Any]:
    """Render canonical marketplace metadata into Claude marketplace shape."""

    return {
        "$schema": CLAUDE_MARKETPLACE_SCHEMA,
        "name": metadata["name"],
        "description": metadata["description"],
        "owner": metadata["owner"].copy(),
        "plugins": [
            {
                "name": plugin["harnesses"]["claude"]["name"],
                "description": plugin["description"],
                "source": plugin["harnesses"]["claude"]["path"],
            }
            for plugin in metadata["plugins"]
            if "claude" in plugin["harnesses"]
        ],
    }


__all__ = ["render_claude_marketplace"]
