from __future__ import annotations

from pathlib import Path


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
