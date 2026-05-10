from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.validators import validate_marketplaces


def _run_python_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_marketplace(root: Path, relative_path: str, data: object) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _minimal_codex_marketplace() -> dict[str, object]:
    return {
        "name": "engine",
        "interface": {"displayName": "Engine"},
        "plugins": [
            {
                "name": "codex-session-memory",
                "source": {"source": "local", "path": "./plugins/codex/session-memory"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Productivity",
            }
        ],
    }


def _minimal_claude_marketplace() -> dict[str, object]:
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "engine",
        "description": "Engine plugins",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "name": "session-memory",
                "description": "Session continuity",
                "source": "./plugins/claude/session-memory",
            }
        ],
    }


def test_validate_marketplaces_rejects_truncated_marketplaces(tmp_path: Path) -> None:
    _write_marketplace(tmp_path, ".agents/plugins/marketplace.json", {"name": "engine"})
    _write_marketplace(tmp_path, ".claude-plugin/marketplace.json", {"name": "engine"})

    errors = validate_marketplaces(tmp_path)

    assert any(".agents/plugins/marketplace.json" in error for error in errors)
    assert any(".claude-plugin/marketplace.json" in error for error in errors)
    assert any("plugins" in error for error in errors)


def test_validate_marketplaces_rejects_codex_plugin_missing_source_path(
    tmp_path: Path,
) -> None:
    codex_marketplace = _minimal_codex_marketplace()
    codex_plugins = codex_marketplace["plugins"]
    assert isinstance(codex_plugins, list)
    codex_plugins[0]["source"] = {"source": "local"}
    _write_marketplace(tmp_path, ".agents/plugins/marketplace.json", codex_marketplace)
    _write_marketplace(
        tmp_path,
        ".claude-plugin/marketplace.json",
        _minimal_claude_marketplace(),
    )

    errors = validate_marketplaces(tmp_path)

    assert any(".agents/plugins/marketplace.json" in error for error in errors)
    assert any("source.path" in error for error in errors)


def test_validate_marketplaces_rejects_claude_owner_missing_name(
    tmp_path: Path,
) -> None:
    claude_marketplace = _minimal_claude_marketplace()
    claude_marketplace["owner"] = {}
    _write_marketplace(tmp_path, ".agents/plugins/marketplace.json", _minimal_codex_marketplace())
    _write_marketplace(tmp_path, ".claude-plugin/marketplace.json", claude_marketplace)

    errors = validate_marketplaces(tmp_path)

    assert any(".claude-plugin/marketplace.json" in error for error in errors)
    assert any("owner.name" in error for error in errors)


def test_build_entrypoint_writes_valid_marketplaces() -> None:
    build = _run_python_script("tools/build_plugins.py")

    assert build.stdout == "built plugin artifacts\n"

    codex_marketplace = json.loads(
        (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )
    claude_marketplace = json.loads(
        (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
    )

    assert codex_marketplace["name"] == "engine"
    assert claude_marketplace["name"] == "engine"
    assert "plugins" in codex_marketplace
    assert "plugins" in claude_marketplace

    validate = _run_python_script("tools/validate_generated.py")

    assert validate.stdout == "generated artifacts valid\n"
