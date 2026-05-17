from __future__ import annotations

import re
import subprocess
from pathlib import Path

from learnable.core.errors import DeniedPathError, PathBoundaryError


_PROJECT_MARKERS = ("AGENTS.md", ".git", ".codex")
_DENIED_EXACT_NAMES = {
    ".env",
    "credentials",
    "credential",
    "key",
    "secret",
    "secrets",
    "token",
    ".token",
}
_DENIED_TOKEN_PARTS = {"credential", "credentials", "key", "secret", "secrets"}
_DENIED_SUFFIXES = {".cert", ".crt", ".key", ".pem", ".pfx", ".p12", ".token"}


def resolve_project_root(start: Path) -> Path:
    candidate = start.resolve()
    if candidate.is_file():
        candidate = candidate.parent

    git_root = _git_project_root(candidate)
    if git_root is not None:
        return git_root

    for current in (candidate, *candidate.parents):
        if any((current / marker).exists() for marker in _PROJECT_MARKERS):
            return current.resolve()
    return candidate


def materials_root(project_root: Path) -> Path:
    root = ensure_within_root(project_root / ".codex" / "materials", project_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def server_state_root(project_root: Path) -> Path:
    root = ensure_within_root(materials_root(project_root) / ".server", project_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_within_root(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve(strict=False)
    if resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root):
        return resolved_path
    raise PathBoundaryError(f"path escapes root: {path}")


def reject_denied_path(path: Path) -> None:
    for part in _relevant_path_parts(path):
        if _is_denied_name(part):
            raise DeniedPathError(f"path is denied: {path}")


def _git_project_root(start: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=False,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return Path(value).resolve() if value else None


def _is_denied_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in _DENIED_EXACT_NAMES or lowered.startswith(".env."):
        return True
    if Path(lowered).suffix in _DENIED_SUFFIXES:
        return True
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    return bool(tokens & _DENIED_TOKEN_PARTS)


def _relevant_path_parts(path: Path) -> tuple[str, ...]:
    if not path.is_absolute():
        return path.parts

    project_root = _nearest_project_marker_root(path)
    if project_root is not None:
        return path.relative_to(project_root).parts

    return (path.name,)


def _nearest_project_marker_root(path: Path) -> Path | None:
    for candidate in path.parents:
        if any((candidate / marker).exists() for marker in _PROJECT_MARKERS):
            return candidate
    return None
