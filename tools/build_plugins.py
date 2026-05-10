from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.claude.marketplaces import render_claude_marketplace
from renderers.codex.marketplaces import render_codex_marketplace
from tools.build.json_io import write_json
from tools.build.metadata import load_marketplace


def main() -> int:
    """Build generated plugin marketplace artifacts."""

    metadata = load_marketplace(ROOT / "plugin-sources/marketplace.yaml")
    write_json(ROOT / ".agents/plugins/marketplace.json", render_codex_marketplace(metadata))
    write_json(ROOT / ".claude-plugin/marketplace.json", render_claude_marketplace(metadata))
    print("built plugin artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
