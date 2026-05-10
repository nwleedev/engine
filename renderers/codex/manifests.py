from __future__ import annotations

from typing import Any


def render_codex_manifest(plugin: dict[str, Any]) -> dict[str, Any]:
    """Render canonical plugin metadata into a Codex plugin manifest."""

    harness = plugin["harnesses"]["codex"]
    manifest = {
        "name": harness["name"],
        "version": str(plugin["version"]),
        "description": plugin["description"],
        "license": plugin["license"],
    }
    if "skills" in harness:
        manifest["skills"] = harness["skills"]

    return manifest


__all__ = ["render_codex_manifest"]
