from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from plugin_manifest_helpers import (
    run_python_script,
    session_memory_plugin,
    write_minimal_generated_root,
    write_path_contract_generated_root,
    write_json,
)
from renderers.claude.manifests import render_claude_manifest
from renderers.codex.manifests import render_codex_manifest
from tools.build.validators import validate_marketplaces


def test_render_codex_manifest_uses_canonical_harness_metadata() -> None:
    manifest = render_codex_manifest(session_memory_plugin())

    assert manifest == {
        "name": "session-memory",
        "version": "0.5.0",
        "description": "Automatic session context narration and injection",
        "license": "MIT",
        "skills": "./skills/",
    }


def test_render_claude_manifest_uses_canonical_harness_metadata() -> None:
    manifest = render_claude_manifest(session_memory_plugin())

    assert manifest == {
        "name": "session-memory",
        "version": "0.5.0",
        "description": "Automatic session context narration and injection",
        "license": "MIT",
    }


def test_build_entrypoint_writes_session_memory_manifests() -> None:
    run_python_script("tools/build_plugins.py")

    codex_manifest = json.loads(
        (
            ROOT / "plugins/codex/session-memory/.codex-plugin/plugin.json"
        ).read_text(encoding="utf-8")
    )
    claude_manifest = json.loads(
        (
            ROOT / "plugins/claude/session-memory/.claude-plugin/plugin.json"
        ).read_text(encoding="utf-8")
    )

    assert codex_manifest["name"] == "session-memory"
    assert claude_manifest["name"] == "session-memory"


def test_validate_marketplaces_reports_missing_generated_plugin_manifest(
    tmp_path: Path,
) -> None:
    write_minimal_generated_root(tmp_path, manifest_name=None)

    errors = validate_marketplaces(tmp_path)

    assert any("missing generated plugin manifest" in error for error in errors)
    assert any(
        "plugins/codex/session-memory/.codex-plugin/plugin.json" in error
        for error in errors
    )


def test_validate_marketplaces_reports_wrong_generated_plugin_manifest_name(
    tmp_path: Path,
) -> None:
    write_minimal_generated_root(tmp_path, manifest_name="wrong-session-memory")

    errors = validate_marketplaces(tmp_path)

    assert any("generated plugin manifest drift" in error for error in errors)
    assert any(
        "plugins/codex/session-memory/.codex-plugin/plugin.json" in error
        for error in errors
    )


def test_validate_marketplaces_reports_codex_skills_manifest_drift(
    tmp_path: Path,
) -> None:
    write_path_contract_generated_root(
        tmp_path,
        codex_manifest_path="plugins/codex-alt/session-memory/.codex-plugin/plugin.json",
        claude_manifest_path="plugins/claude-alt/session-memory/.claude-plugin/plugin.json",
    )
    write_json(
        tmp_path,
        "plugins/codex-alt/session-memory/.codex-plugin/plugin.json",
        {
            "name": "session-memory",
            "version": "0.0.0",
            "description": "Automatic session context narration and injection",
            "license": "MIT",
            "skills": "./stale-skills/",
        },
    )

    errors = validate_marketplaces(tmp_path)

    assert any("generated plugin manifest drift" in error for error in errors)
    assert any(
        "plugins/codex-alt/session-memory/.codex-plugin/plugin.json" in error
        for error in errors
    )


def test_validate_marketplaces_reports_stale_generated_plugin_manifest_payload(
    tmp_path: Path,
) -> None:
    write_minimal_generated_root(tmp_path, manifest_name="session-memory")
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.codex-plugin/plugin.json",
        {
            "name": "session-memory",
            "version": "0.0.0",
            "description": "Automatic session context narration and injection",
            "license": "MIT",
        },
    )

    errors = validate_marketplaces(tmp_path)

    assert any("generated plugin manifest drift" in error for error in errors)
    assert any(
        "plugins/codex/session-memory/.codex-plugin/plugin.json" in error
        for error in errors
    )


def test_validate_marketplaces_reports_codex_marketplace_drift(
    tmp_path: Path,
) -> None:
    write_minimal_generated_root(tmp_path, manifest_name="session-memory")
    write_json(
        tmp_path,
        ".agents/plugins/marketplace.json",
        {
            "name": "engine",
            "interface": {"displayName": "Engine"},
            "plugins": [
                {
                    "name": "session-memory",
                    "source": {
                        "source": "local",
                        "path": "./plugins/codex/stale-session-memory",
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

    errors = validate_marketplaces(tmp_path)

    assert "generated marketplace drift: .agents/plugins/marketplace.json" in errors


def test_validate_marketplaces_reports_claude_marketplace_drift(
    tmp_path: Path,
) -> None:
    write_path_contract_generated_root(
        tmp_path,
        codex_manifest_path="plugins/codex-alt/session-memory/.codex-plugin/plugin.json",
        claude_manifest_path="plugins/claude-alt/session-memory/.claude-plugin/plugin.json",
    )
    write_json(
        tmp_path,
        ".claude-plugin/marketplace.json",
        {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "engine",
            "description": "Minimal metadata",
            "owner": {"name": "nwleedev"},
            "plugins": [
                {
                    "name": "session-memory",
                    "description": "Session continuity",
                    "source": "./plugins/claude/session-memory",
                }
            ],
        },
    )

    errors = validate_marketplaces(tmp_path)

    assert "generated marketplace drift: .claude-plugin/marketplace.json" in errors


def test_validate_marketplaces_uses_metadata_harness_paths_for_plugin_manifests(
    tmp_path: Path,
) -> None:
    write_path_contract_generated_root(
        tmp_path,
        codex_manifest_path="plugins/codex-alt/session-memory/.codex-plugin/plugin.json",
        claude_manifest_path="plugins/claude-alt/session-memory/.claude-plugin/plugin.json",
    )

    errors = validate_marketplaces(tmp_path)

    assert errors == []


def test_validate_marketplaces_rejects_manifests_only_at_legacy_hardcoded_paths(
    tmp_path: Path,
) -> None:
    write_path_contract_generated_root(
        tmp_path,
        codex_manifest_path="plugins/codex/session-memory/.codex-plugin/plugin.json",
        claude_manifest_path="plugins/claude/session-memory/.claude-plugin/plugin.json",
    )

    errors = validate_marketplaces(tmp_path)

    assert any(
        "plugins/codex-alt/session-memory/.codex-plugin/plugin.json" in error
        for error in errors
    )
    assert any(
        "plugins/claude-alt/session-memory/.claude-plugin/plugin.json" in error
        for error in errors
    )
