from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# pytest importlib mode does not add the project root for this interop import.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build import paths as build_paths
from tools.build.headers import markdown_header, python_header


def test_build_paths_define_canonical_targets() -> None:
    assert build_paths.ROOT == ROOT
    assert build_paths.PLUGIN_SOURCES == ROOT / "plugin-sources"
    assert build_paths.PACKAGES == ROOT / "packages"
    assert build_paths.RENDERERS == ROOT / "renderers"
    assert build_paths.GENERATED_PLUGINS == ROOT / "plugins"
    assert build_paths.CODEX_PLUGINS == ROOT / "plugins" / "codex"
    assert build_paths.CLAUDE_PLUGINS == ROOT / "plugins" / "claude"
    assert build_paths.SNAPSHOTS == ROOT / "tests" / "snapshots"
    assert build_paths.INTEROP_TESTS == ROOT / "tests" / "interop"


def test_markdown_header_includes_notice_and_source() -> None:
    header = markdown_header("plugin-sources/shared-subagents/agents/code-mapper.toml")

    assert header == (
        "<!-- GENERATED FILE - DO NOT EDIT -->\n"
        "<!-- source: plugin-sources/shared-subagents/agents/code-mapper.toml -->\n\n"
    )


def test_python_header_includes_notice_and_source() -> None:
    header = python_header("plugin-sources/shared-subagents/agents/code-mapper.toml")

    assert header == (
        "# GENERATED FILE - DO NOT EDIT\n"
        "# source: plugin-sources/shared-subagents/agents/code-mapper.toml\n\n"
    )
