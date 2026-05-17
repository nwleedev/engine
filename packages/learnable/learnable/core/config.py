from __future__ import annotations

import json
import secrets
from collections.abc import Mapping
from pathlib import Path

from learnable.core.paths import ensure_within_root, server_state_root


def default_server_config(project_root: Path) -> dict[str, object]:
    materials = _materials_path(project_root)
    server_root = _server_state_path(project_root)
    return {
        "projectRoot": str(project_root.resolve()),
        "materialsRoot": str(materials),
        "serverStateRoot": str(server_root),
        "configPath": str(_config_path(project_root)),
        "tokenPath": str(_token_path(project_root)),
        "auditLogPath": str(_audit_log_path(project_root)),
    }


def write_server_config(project_root: Path, config: Mapping[str, object]) -> Path:
    server_root = server_state_root(project_root)
    config_path = ensure_within_root(server_root / "config.json", project_root)
    token_path = _token_path(project_root)
    audit_log_path = _audit_log_path(project_root)

    config_path.write_text(
        json.dumps(dict(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    audit_log_path.touch(exist_ok=True)
    return config_path


def read_server_config(project_root: Path) -> dict[str, object]:
    config_path = _config_path(project_root)
    return json.loads(config_path.read_text(encoding="utf-8"))


def _materials_path(project_root: Path) -> Path:
    return ensure_within_root(project_root / ".codex" / "materials", project_root)


def _server_state_path(project_root: Path) -> Path:
    return ensure_within_root(_materials_path(project_root) / ".server", project_root)


def _config_path(project_root: Path) -> Path:
    return ensure_within_root(_server_state_path(project_root) / "config.json", project_root)


def _token_path(project_root: Path) -> Path:
    return ensure_within_root(_server_state_path(project_root) / "token", project_root)


def _audit_log_path(project_root: Path) -> Path:
    return ensure_within_root(_server_state_path(project_root) / "audits.jsonl", project_root)
