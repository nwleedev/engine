from __future__ import annotations

from pathlib import Path

import pytest

from learnable.core.errors import DeniedPathError, PathBoundaryError
from learnable.core.paths import (
    ensure_within_root,
    materials_root,
    reject_denied_path,
    resolve_project_root,
    server_state_root,
)


def test_resolve_project_root_finds_nearest_project_marker(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    nested = project_root / "packages" / "learnable"
    nested.mkdir(parents=True)
    (project_root / "AGENTS.md").write_text("# project\n", encoding="utf-8")

    assert resolve_project_root(nested) == project_root.resolve()


def test_materials_and_server_roots_are_created_under_codex(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    assert materials_root(root) == (root / ".codex" / "materials").resolve()
    assert server_state_root(root) == (root / ".codex" / "materials" / ".server").resolve()
    assert (root / ".codex" / "materials").is_dir()
    assert (root / ".codex" / "materials" / ".server").is_dir()


def test_ensure_within_root_rejects_parent_escape(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(PathBoundaryError):
        ensure_within_root(root / ".." / "outside.txt", root)


def test_ensure_within_root_rejects_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathBoundaryError):
        ensure_within_root(root / "linked" / "secret.txt", root)


@pytest.mark.parametrize(
    "relative_path",
    [
        ".env",
        ".env.local",
        ".codex/materials/.server/token",
        "secrets/service.key",
        "private/certificate.pem",
        "config/api-credentials.json",
    ],
)
def test_reject_denied_path_blocks_sensitive_paths(
    tmp_path: Path, relative_path: str
) -> None:
    with pytest.raises(DeniedPathError):
        reject_denied_path(tmp_path / relative_path)


@pytest.mark.parametrize(
    "relative_path",
    [
        "notes/tokenized-learning.md",
        "docs/token-budget.md",
        "docs/api-token-usage.md",
        "docs/keynote-outline.md",
        ".codex/materials/.server/config.json",
        ".codex/materials/.server/audits.jsonl",
    ],
)
def test_reject_denied_path_allows_neutral_paths(
    tmp_path: Path, relative_path: str
) -> None:
    reject_denied_path(tmp_path / relative_path)


def test_reject_denied_path_ignores_sensitive_absolute_ancestors(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "secrets" / "project"
    project_root.mkdir(parents=True)
    (project_root / "AGENTS.md").write_text("# project\n", encoding="utf-8")

    reject_denied_path(project_root / "docs" / "token-budget.md")


def test_reject_denied_path_allows_markerless_absolute_neutral_file_under_secrets(
    tmp_path: Path,
) -> None:
    absolute_parent = tmp_path / "secrets"
    absolute_parent.mkdir()

    reject_denied_path(absolute_parent / "token-budget.md")


def test_reject_denied_path_allows_relative_neutral_token_topic_path() -> None:
    reject_denied_path(Path("docs/token-budget.md"))


def test_reject_denied_path_blocks_relative_sensitive_directory_path() -> None:
    with pytest.raises(DeniedPathError):
        reject_denied_path(Path("secrets/token-budget.md"))


@pytest.mark.parametrize(
    "relative_path",
    [
        "token",
        ".token",
        "access.token",
        "secrets/token-budget.md",
    ],
)
def test_reject_denied_path_blocks_secret_like_token_paths(
    tmp_path: Path, relative_path: str
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("# project\n", encoding="utf-8")

    with pytest.raises(DeniedPathError):
        reject_denied_path(project_root / relative_path)
