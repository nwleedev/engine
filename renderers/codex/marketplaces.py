from __future__ import annotations

from typing import Any


def render_codex_marketplace(metadata: dict[str, Any]) -> dict[str, Any]:
    """Render canonical marketplace metadata into Codex marketplace shape."""

    return {
        "name": metadata["name"],
        "interface": {"displayName": metadata["display_name"]},
        "plugins": [
            {
                "name": plugin["harnesses"]["codex"]["name"],
                "source": {
                    "source": "local",
                    "path": plugin["harnesses"]["codex"]["path"],
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": plugin["category"],
            }
            for plugin in metadata["plugins"]
            if "codex" in plugin["harnesses"]
        ],
    }


__all__ = ["render_codex_marketplace"]
