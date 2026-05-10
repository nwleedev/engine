from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

# These constants define canonical target paths; later migration tasks create
# some of these directories when they move the corresponding sources.
PLUGIN_SOURCES = ROOT / "plugin-sources"
PACKAGES = ROOT / "packages"
RENDERERS = ROOT / "renderers"
GENERATED_PLUGINS = ROOT / "plugins"
CODEX_PLUGINS = GENERATED_PLUGINS / "codex"
CLAUDE_PLUGINS = GENERATED_PLUGINS / "claude"
SNAPSHOTS = ROOT / "tests" / "snapshots"
INTEROP_TESTS = ROOT / "tests" / "interop"

_MANIFEST_PATH_BY_HARNESS = {
    "claude": Path(".claude-plugin/plugin.json"),
    "codex": Path(".codex-plugin/plugin.json"),
}


def normalize_harness_path(path: str) -> Path:
    """Return a repo-relative harness path from canonical metadata."""

    if path.strip() == "":
        raise ValueError("harness path must not be empty")

    relative_path = Path(path)
    if relative_path == Path("."):
        raise ValueError("harness path must not point to repository root")
    if relative_path.is_absolute():
        raise ValueError(f"harness path must be relative: {path}")
    if ".." in relative_path.parts:
        raise ValueError(f"harness path must not escape the repository: {path}")

    return relative_path


def plugin_manifest_path(plugin: dict[str, Any], harness_name: str) -> Path:
    """Return the repo-relative generated manifest path for a plugin harness."""

    try:
        harness = plugin["harnesses"][harness_name]
        manifest_suffix = _MANIFEST_PATH_BY_HARNESS[harness_name]
    except KeyError as exc:
        raise ValueError(f"unsupported plugin harness: {harness_name}") from exc

    return normalize_harness_path(harness["path"]) / manifest_suffix
