from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnable.core.config import (
    default_server_config,
    read_server_config,
    write_server_config,
)


def test_default_server_config_uses_private_server_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    config = default_server_config(project_root)

    assert config["materialsRoot"] == str(
        (project_root / ".codex" / "materials").resolve()
    )
    assert config["serverStateRoot"] == str(
        (project_root / ".codex" / "materials" / ".server").resolve()
    )
    assert config["tokenPath"] == str(
        (project_root / ".codex" / "materials" / ".server" / "token").resolve()
    )
    assert config["auditLogPath"] == str(
        (project_root / ".codex" / "materials" / ".server" / "audits.jsonl").resolve()
    )


def test_default_server_config_does_not_create_server_directories(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    default_server_config(project_root)

    assert not (project_root / ".codex" / "materials").exists()
    assert not (project_root / ".codex" / "materials" / ".server").exists()


def test_read_server_config_does_not_create_directories_when_config_is_absent(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()

    with pytest.raises(FileNotFoundError):
        read_server_config(project_root)

    assert not (project_root / ".codex" / "materials").exists()
    assert not (project_root / ".codex" / "materials" / ".server").exists()


def test_write_server_config_creates_config_token_and_audit_paths(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config = default_server_config(project_root) | {"host": "127.0.0.1", "port": 48732}

    config_path = write_server_config(project_root, config)

    server_root = project_root / ".codex" / "materials" / ".server"
    assert config_path == (server_root / "config.json").resolve()
    assert (server_root / "config.json").is_file()
    assert (server_root / "token").is_file()
    assert (server_root / "audits.jsonl").is_file()
    assert json.loads((server_root / "config.json").read_text(encoding="utf-8")) == config
    assert (server_root / "token").read_text(encoding="utf-8").strip()
    assert (server_root / "audits.jsonl").read_text(encoding="utf-8") == ""


def test_read_server_config_returns_existing_config(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    expected = default_server_config(project_root) | {"host": "127.0.0.1", "port": 48732}
    write_server_config(project_root, expected)

    assert read_server_config(project_root) == expected
