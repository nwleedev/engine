import json
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"


def test_plugin_manifest_is_skill_only():
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())

    assert manifest["name"] == "codex-session-memory"
    assert manifest["skills"] == "./skills/"
    assert "hooks" not in manifest
    assert "automatic hooks" not in manifest["description"].lower()
