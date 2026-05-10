from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# pytest importlib mode does not add the project root for this interop import.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.materialize import replace_tree, write_text_tree


def test_unsafe_target_outside_generated_roots_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "session-memory"

    with pytest.raises(ValueError, match="outside generated plugin root"):
        write_text_tree(tmp_path, target, {"README.md": "unsafe\n"})


@pytest.mark.parametrize("harness", ["codex", "claude"])
def test_harness_root_target_is_rejected(tmp_path: Path, harness: str) -> None:
    target = tmp_path / "plugins" / harness

    with pytest.raises(ValueError, match="outside generated plugin root"):
        write_text_tree(tmp_path, target, {"README.md": "unsafe\n"})


def test_write_text_tree_removes_stale_files_and_writes_new_content(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    write_text_tree(
        tmp_path,
        target,
        {
            "nested/b.md": "second\n",
            "a.md": "first\n",
        },
    )

    assert not stale.exists()
    assert (target / "a.md").read_text(encoding="utf-8") == "first\n"
    assert (target / "nested" / "b.md").read_text(encoding="utf-8") == "second\n"


def test_replace_tree_rejects_non_canonical_source(tmp_path: Path) -> None:
    source = tmp_path / "external" / "source"
    source.mkdir(parents=True)
    target = tmp_path / "plugins" / "codex" / "sample"

    with pytest.raises(ValueError, match="outside canonical source roots"):
        replace_tree(tmp_path, source, target)


def test_replace_tree_rejects_missing_canonical_source_and_preserves_target(tmp_path: Path) -> None:
    source = tmp_path / "plugin-sources" / "missing"
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical source is not a directory"):
        replace_tree(tmp_path, source, target)

    assert stale.read_text(encoding="utf-8") == "old\n"


def test_replace_tree_rejects_file_canonical_source_and_preserves_target(tmp_path: Path) -> None:
    source = tmp_path / "plugin-sources" / "source.md"
    source.parent.mkdir(parents=True)
    source.write_text("file\n", encoding="utf-8")
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical source is not a directory"):
        replace_tree(tmp_path, source, target)

    assert stale.read_text(encoding="utf-8") == "old\n"


def test_replace_tree_copies_canonical_source_and_removes_stale_target(tmp_path: Path) -> None:
    source = tmp_path / "plugin-sources" / "sample"
    source.mkdir(parents=True)
    (source / "README.md").write_text("new\n", encoding="utf-8")
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    replace_tree(tmp_path, source, target)

    assert not stale.exists()
    assert (target / "README.md").read_text(encoding="utf-8") == "new\n"


def test_replace_tree_rejects_source_file_symlink_and_preserves_target(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external.md"
    external.write_text("outside\n", encoding="utf-8")
    source = tmp_path / "plugin-sources" / "sample"
    source.mkdir(parents=True)
    (source / "linked.md").symlink_to(external)
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical source must not contain symlinks"):
        replace_tree(tmp_path, source, target)

    assert stale.read_text(encoding="utf-8") == "old\n"


def test_replace_tree_rejects_source_directory_symlink_and_preserves_target(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (external / "outside.md").write_text("outside\n", encoding="utf-8")
    source = tmp_path / "plugin-sources" / "sample"
    source.mkdir(parents=True)
    (source / "linked").symlink_to(external, target_is_directory=True)
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical source must not contain symlinks"):
        replace_tree(tmp_path, source, target)

    assert stale.read_text(encoding="utf-8") == "old\n"


def test_target_under_codex_plugin_root_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "codex" / "sample"

    write_text_tree(tmp_path, target, {"README.md": "ok\n"})

    assert (target / "README.md").read_text(encoding="utf-8") == "ok\n"


def test_write_text_tree_rejects_file_keys_that_escape_target(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "codex" / "sample"

    with pytest.raises(ValueError, match="outside target tree"):
        write_text_tree(tmp_path, target, {"../escape.md": "unsafe\n"})


def test_write_text_tree_rejects_absolute_file_key_before_replacing_target(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside target tree"):
        write_text_tree(tmp_path, target, {str(tmp_path / "escape.md"): "unsafe\n"})

    assert stale.read_text(encoding="utf-8") == "old\n"


def test_write_text_tree_rejects_late_invalid_key_before_partial_write(tmp_path: Path) -> None:
    target = tmp_path / "plugins" / "codex" / "sample"
    stale = target / "stale.md"
    new_file = target / "a.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside target tree"):
        write_text_tree(
            tmp_path,
            target,
            {
                "a.md": "new\n",
                "nested/../../escape.md": "unsafe\n",
            },
        )

    assert stale.read_text(encoding="utf-8") == "old\n"
    assert not new_file.exists()
