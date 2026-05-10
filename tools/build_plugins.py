from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.claude.manifests import render_claude_manifest
from renderers.claude.marketplaces import render_claude_marketplace
from renderers.codex.manifests import render_codex_manifest
from renderers.codex.marketplaces import render_codex_marketplace
from tools.build.json_io import write_json
from tools.build.metadata import load_marketplace
from tools.build.paths import plugin_manifest_path


def main() -> int:
    """Build generated plugin marketplace artifacts."""

    metadata = load_marketplace(ROOT / "plugin-sources/marketplace.yaml")
    write_json(ROOT / ".agents/plugins/marketplace.json", render_codex_marketplace(metadata))
    write_json(ROOT / ".claude-plugin/marketplace.json", render_claude_marketplace(metadata))
    for plugin in metadata["plugins"]:
        harnesses = plugin["harnesses"]
        if "codex" in harnesses:
            write_json(
                ROOT / plugin_manifest_path(plugin, "codex"),
                render_codex_manifest(plugin),
            )
        if "claude" in harnesses:
            write_json(
                ROOT / plugin_manifest_path(plugin, "claude"),
                render_claude_manifest(plugin),
            )
    print("built plugin artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
