from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ROOT / "packages"

FORBIDDEN_IMPORT_ROOTS = (
    "plugins",
    "plugin_sources",
    "renderers",
    "tools.build",
)

FORBIDDEN_RUNTIME_MARKERS = (
    "CLAUDE_PLUGIN_ROOT",
    "CLAUDE_PROJECT_DIR",
    "CODEX_THREAD_ID",
    ".claude",
    ".codex",
    "hooks/",
    "commands/",
    "skills/",
)

FORBIDDEN_PLUGIN_LAYER_STRINGS = ("plugin-sources",)


def test_imported_modules_includes_relative_alias_imports() -> None:
    source = """
from . import plugins
from .. import plugin_sources
from . import renderers
"""
    tree = ast.parse(source)

    modules = _imported_modules(tree)

    assert _has_forbidden_import("plugins")
    assert _has_forbidden_import("plugin_sources")
    assert _has_forbidden_import("renderers")
    assert "plugins" in modules
    assert "plugin_sources" in modules
    assert "renderers" in modules


def test_imported_modules_includes_normal_import_aliases() -> None:
    source = """
import plugins.foo as foo
import plugin_sources as ps
import renderers.codex
"""
    tree = ast.parse(source)

    modules = _imported_modules(tree)

    assert "plugins.foo" in modules
    assert "plugin_sources" in modules
    assert "renderers.codex" in modules
    assert _has_forbidden_import("plugins.foo")
    assert _has_forbidden_import("plugin_sources")
    assert _has_forbidden_import("renderers.codex")


def test_imported_modules_includes_from_import_alias_candidates() -> None:
    source = """
from tools import build
"""
    tree = ast.parse(source)

    modules = _imported_modules(tree)

    assert "tools.build" in modules
    assert _has_forbidden_import("tools.build")


def test_runtime_markers_match_task_10_plan_scope() -> None:
    assert FORBIDDEN_RUNTIME_MARKERS == (
        "CLAUDE_PLUGIN_ROOT",
        "CLAUDE_PROJECT_DIR",
        "CODEX_THREAD_ID",
        ".claude",
        ".codex",
        "hooks/",
        "commands/",
        "skills/",
    )


def test_forbidden_plugin_layer_strings_match_plugin_sources_paths() -> None:
    assert _forbidden_plugin_layer_strings('Path("plugin-sources")') == [
        "plugin-sources"
    ]
    assert _forbidden_plugin_layer_strings('"plugin-sources/marketplace.yaml"') == [
        "plugin-sources"
    ]


def _package_python_files() -> list[Path]:
    if not PACKAGES.exists():
        return []
    return sorted(PACKAGES.rglob("*.py"))


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
                modules.extend(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
            else:
                modules.extend(alias.name for alias in node.names)
    return modules


def _has_forbidden_import(module: str) -> bool:
    return any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_IMPORT_ROOTS
    )


def _forbidden_plugin_layer_strings(text: str) -> list[str]:
    return [
        marker for marker in FORBIDDEN_PLUGIN_LAYER_STRINGS if marker in text
    ]


def test_packages_do_not_import_plugin_layers() -> None:
    violations: list[str] = []

    for path in _package_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _imported_modules(tree):
            if _has_forbidden_import(module):
                violations.append(f"{path.relative_to(ROOT)} imports {module}")

    assert violations == []


def test_packages_do_not_contain_runtime_markers() -> None:
    violations: list[str] = []

    for path in _package_python_files():
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)} contains {marker}")
        for marker in _forbidden_plugin_layer_strings(text):
            violations.append(f"{path.relative_to(ROOT)} contains {marker}")

    assert violations == []
