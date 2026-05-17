from __future__ import annotations

from pathlib import Path

import pytest

from learnable.cli import main
from learnable.core.errors import DeniedPathError, PathBoundaryError
from learnable.core.paths import ensure_within_root, reject_denied_path
from learnable.web.static import read_static_resource


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "packages" / "learnable" / "learnable"


def test_scn_lrn_011_004_runtime_has_no_session_memory_checkpoint_invocation() -> None:
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE_ROOT.rglob("*.py")
        if path.is_file()
    )

    assert "session-memory" not in runtime_text
    assert "$session-memory:checkpoint" not in runtime_text
    assert "checkpoint" not in runtime_text


def test_scn_lrn_011_005_path_security_guards_reject_sensitive_inputs(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / "linked-outside"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathBoundaryError):
        ensure_within_root(link / "secret.txt", tmp_path)
    with pytest.raises(DeniedPathError):
        reject_denied_path(tmp_path / ".env")


def test_scn_lrn_011_006_static_ui_excludes_browser_generation_surfaces() -> None:
    html = read_static_resource("index.html")[0].decode("utf-8").lower()
    js = read_static_resource("app.js")[0].decode("utf-8").lower()

    assert "<textarea" not in html
    assert "contenteditable" not in html
    assert "/api/ask" not in js
    assert "/api/explain" not in js
    assert "websocket" not in html + js
    assert "eventsource" not in html + js


def test_scn_lrn_011_007_cli_excludes_storage_migration_commands() -> None:
    for command in ["migrate", "export", "reindex"]:
        assert main([command]) == 2
