from __future__ import annotations

from pathlib import Path


CANONICAL_SOURCE_ROOTS = ("plugin-sources", "packages")


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return whether path is equal to or inside parent."""

    return path == parent or path.is_relative_to(parent)


def _resolve_from_root(root: Path, path: Path) -> Path:
    """Return an absolute path, treating relative inputs as root-relative."""

    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _containing_canonical_root(root: Path, path: Path) -> Path | None:
    """Return the canonical source root containing a lexical source path."""

    resolved_root = root.resolve()
    absolute_path = path if path.is_absolute() else root / path

    for source_name in CANONICAL_SOURCE_ROOTS:
        source_root = resolved_root / source_name
        try:
            if _is_relative_to(absolute_path.resolve().parent, source_root):
                return source_root
        except OSError:
            continue
        if _is_relative_to(absolute_path.absolute(), source_root):
            return source_root
    return None


def _has_symlink_segment(path: Path, boundary: Path) -> bool:
    """Return whether path or an ancestor between boundary and path is a symlink."""

    current = path
    while True:
        if current.is_symlink():
            return True
        if current == boundary:
            return False
        if current.parent == current:
            return False
        current = current.parent


def ensure_source_file(root: Path, path: Path) -> Path:
    """Validate and return a real canonical source file without symlink escapes."""

    resolved_root = root.resolve()
    absolute_path = path if path.is_absolute() else resolved_root / path
    canonical_root = _containing_canonical_root(resolved_root, absolute_path)
    boundary = canonical_root if canonical_root is not None else resolved_root

    if _has_symlink_segment(absolute_path, boundary):
        raise ValueError(f"canonical source file must not be a symlink: {path}")

    resolved_path = _resolve_from_root(resolved_root, path)
    if canonical_root is not None and not _is_relative_to(resolved_path, canonical_root):
        raise ValueError(f"canonical source file escapes source root: {path}")

    if not resolved_path.is_file():
        raise ValueError(f"expected file: {path}")

    return absolute_path


def source_file_exists(root: Path, path: Path) -> bool:
    """Return whether path is a valid canonical source file."""

    try:
        ensure_source_file(root, path)
    except (OSError, ValueError):
        return False
    return True


__all__ = ["ensure_source_file", "source_file_exists"]
