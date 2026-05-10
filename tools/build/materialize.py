from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path


IGNORED_COPY_TREE_NAMES = frozenset({"__pycache__"})
IGNORED_COPY_TREE_SUFFIXES = frozenset({".pyc", ".pyo"})


def _resolve_from_root(root: Path, path: Path) -> Path:
    """Return an absolute path, treating relative inputs as root-relative."""

    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return whether path is equal to or inside parent."""

    return path == parent or path.is_relative_to(parent)


def _remove_existing(path: Path) -> None:
    """Remove an existing file, symlink, or directory tree."""

    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.exists():
        shutil.rmtree(path)


def ensure_generated_target(root: Path, target: Path) -> Path:
    """Validate and return a destructive target under generated plugin roots."""

    resolved_root = Path(root).resolve()
    resolved_target = _resolve_from_root(resolved_root, Path(target))
    generated_roots = (
        resolved_root / "plugins" / "codex",
        resolved_root / "plugins" / "claude",
    )

    if not any(_is_relative_to(resolved_target, generated_root) for generated_root in generated_roots):
        raise ValueError(f"outside generated plugin root: {target}")

    return resolved_target


def _ensure_canonical_source(root: Path, source: Path) -> Path:
    """Validate and return a source under canonical source roots."""

    resolved_root = Path(root).resolve()
    resolved_source = _resolve_from_root(resolved_root, Path(source))
    source_roots = (
        resolved_root / "plugin-sources",
        resolved_root / "packages",
    )

    if not any(_is_relative_to(resolved_source, source_root) for source_root in source_roots):
        raise ValueError(f"outside canonical source roots: {source}")

    if not resolved_source.is_dir():
        raise ValueError(f"canonical source is not a directory: {source}")

    return resolved_source


def _ensure_source_tree_has_no_symlinks(source: Path) -> None:
    """Reject symlinks before copying canonical source into generated output."""

    for entry in source.rglob("*"):
        if entry.is_symlink():
            raise ValueError(f"canonical source must not contain symlinks: {entry}")


def _ignore_copy_tree_noise(_directory: str, names: list[str]) -> set[str]:
    """Return transient Python cache entries to omit from generated artifacts."""

    return {
        name
        for name in names
        if name in IGNORED_COPY_TREE_NAMES
        or Path(name).suffix in IGNORED_COPY_TREE_SUFFIXES
    }


def replace_tree(root: Path, source: Path, target: Path) -> None:
    """Replace a generated plugin target tree with a canonical source tree."""

    resolved_target = ensure_generated_target(root, target)
    resolved_source = _ensure_canonical_source(root, source)
    _ensure_source_tree_has_no_symlinks(resolved_source)

    _remove_existing(resolved_target)
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        resolved_source,
        resolved_target,
        ignore=_ignore_copy_tree_noise,
    )


def _safe_text_path(target: Path, relative_path: str) -> Path:
    """Return a target child path, rejecting absolute or parent traversal keys."""

    path = Path(relative_path)
    if path == Path(".") or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"outside target tree: {relative_path}")

    destination = (target / path).resolve()
    if not _is_relative_to(destination, target):
        raise ValueError(f"outside target tree: {relative_path}")

    return destination


def write_text_tree(root: Path, target: Path, files: Mapping[str, str]) -> None:
    """Replace a generated plugin target tree with deterministic UTF-8 text files."""

    resolved_target = ensure_generated_target(root, target)
    resolved_files = [
        (relative_path, _safe_text_path(resolved_target, relative_path))
        for relative_path in sorted(files)
    ]

    _remove_existing(resolved_target)
    for relative_path, destination in resolved_files:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(files[relative_path], encoding="utf-8")


__all__ = ["ensure_generated_target", "replace_tree", "write_text_tree"]
