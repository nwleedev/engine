from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from marketplace_metadata_helpers import minimal_marketplace_lines


ROOT = Path(__file__).resolve().parents[2]


def run_python_script(script: str) -> subprocess.CompletedProcess[str]:
    """Run a repository Python entrypoint from the project root."""

    return subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def session_memory_plugin() -> dict[str, Any]:
    """Return canonical session-memory metadata for manifest renderer tests."""

    return {
        "id": "session-memory",
        "version": "0.4.0",
        "description": "Automatic session context narration and injection",
        "license": "MIT",
        "category": "Productivity",
        "harnesses": {
            "claude": {
                "name": "session-memory",
                "path": "./plugins/claude/session-memory",
            },
            "codex": {
                "name": "codex-session-memory",
                "skills": "./skills/",
                "path": "./plugins/codex/session-memory",
            },
        },
    }


def write_json(root: Path, relative_path: str, data: object) -> None:
    """Write indented-free JSON fixtures under a temporary generated root."""

    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def write_minimal_generated_root(root: Path, manifest_name: str | None) -> None:
    """Write a minimal generated marketplace tree for validator tests."""

    metadata = root / "plugin-sources" / "marketplace.yaml"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text("\n".join(minimal_marketplace_lines()), encoding="utf-8")

    write_json(
        root,
        ".agents/plugins/marketplace.json",
        {
            "name": "engine",
            "interface": {"displayName": "Engine"},
            "plugins": [
                {
                    "name": "codex-session-memory",
                    "source": {
                        "source": "local",
                        "path": "./plugins/codex/session-memory",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        },
    )
    write_json(
        root,
        ".claude-plugin/marketplace.json",
        {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "engine",
            "description": "Minimal metadata",
            "owner": {"name": "nwleedev"},
            "plugins": [],
        },
    )
    if manifest_name is not None:
        write_json(
            root,
            "plugins/codex/session-memory/.codex-plugin/plugin.json",
            {
                "name": manifest_name,
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
            },
        )


def write_path_contract_generated_root(
    root: Path,
    *,
    codex_manifest_path: str | None,
    claude_manifest_path: str | None,
) -> None:
    """Write a generated tree whose harness paths differ from legacy paths."""

    metadata = root / "plugin-sources" / "marketplace.yaml"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Minimal metadata",
                "owner:",
                "  name: nwleedev",
                "plugins:",
                "  - id: session-memory",
                "    version: 0.4.0",
                "    description: Automatic session context narration and injection",
                "    license: MIT",
                "    category: Productivity",
                "    harnesses:",
                "      codex:",
                "        name: codex-session-memory",
                "        skills: ./skills/",
                "        path: ./plugins/codex-alt/session-memory",
                "      claude:",
                "        name: session-memory",
                "        path: ./plugins/claude-alt/session-memory",
            ]
        ),
        encoding="utf-8",
    )

    write_json(
        root,
        ".agents/plugins/marketplace.json",
        {
            "name": "engine",
            "interface": {"displayName": "Engine"},
            "plugins": [
                {
                    "name": "codex-session-memory",
                    "source": {
                        "source": "local",
                        "path": "./plugins/codex-alt/session-memory",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        },
    )
    write_json(
        root,
        ".claude-plugin/marketplace.json",
        {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "engine",
            "description": "Minimal metadata",
            "owner": {"name": "nwleedev"},
            "plugins": [
                {
                    "name": "session-memory",
                    "description": "Automatic session context narration and injection",
                    "source": "./plugins/claude-alt/session-memory",
                }
            ],
        },
    )
    if codex_manifest_path is not None:
        write_json(
            root,
            codex_manifest_path,
            {
                "name": "codex-session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "skills": "./skills/",
            },
        )
    if claude_manifest_path is not None:
        write_json(
            root,
            claude_manifest_path,
            {
                "name": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
            },
        )
