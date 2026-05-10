from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


def test_marketplace_exposes_shared_subagents() -> None:
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))

    plugin = next(
        item for item in data["plugins"] if item["name"] == "shared-subagents"
    )

    assert plugin["source"] == {
        "source": "local",
        "path": "./plugins/codex/shared-subagents",
    }
    assert plugin["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert plugin["category"] == "Productivity"
