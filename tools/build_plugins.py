from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.claude.manifests import render_claude_manifest
from renderers.claude.marketplaces import render_claude_marketplace
from renderers.claude.skills import render_claude_skill_tree
from renderers.claude.subagents import render_claude_agent_tree
from renderers.codex.manifests import render_codex_manifest
from renderers.codex.marketplaces import render_codex_marketplace
from renderers.codex.skills import render_codex_skill_tree
from renderers.codex.subagents import render_codex_agent_tree
from renderers.plugin_tree import render_plugin_text_tree
from tools.build.generated_registry import registry_document, registry_entry
from tools.build.json_io import write_json
from tools.build.materialize import replace_tree, write_text_tree
from tools.build.metadata import load_marketplace
from tools.build.paths import plugin_manifest_path


COPIED_TREE_TRACEABLE_SUFFIXES = frozenset({".json", ".md", ".py", ".toml"})
GENERATED_MANIFEST_TARGETS = frozenset(
    {
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
    }
)
MARKETPLACE_SOURCE = "plugin-sources/marketplace.yaml"
PackageArtifact = tuple[Path, Path, str]
STALE_GENERATED_PLUGIN_ROOTS = (
    Path("plugins/codex/research-prompt"),
    Path("plugins/claude/research-prompt"),
)


def _registry_entries_for_copied_tree(
    source_root: Path,
    target_prefix: str = "",
) -> list[dict[str, str]]:
    """Return generated registry entries for raw copied adapter files."""

    return [
        registry_entry(
            f"{target_prefix}{source_path.relative_to(source_root).as_posix()}",
            source_path.relative_to(ROOT).as_posix(),
        )
        for source_path in sorted(source_root.rglob("*"))
        if source_path.is_file()
        and source_path.suffix in COPIED_TREE_TRACEABLE_SUFFIXES
        and source_path.relative_to(source_root).as_posix()
        not in GENERATED_MANIFEST_TARGETS
    ]


def _package_license_source(source_root: Path) -> Path | None:
    """Return the package-level license file that must follow vendored code."""

    license_source = source_root.parent / "LICENSE"
    if license_source.is_file():
        return license_source
    return None


def _copy_package_license(source_root: Path, target_root: Path) -> None:
    """Copy a package-level license notice into the materialized package."""

    license_source = _package_license_source(source_root)
    if license_source is None:
        return

    (target_root / "LICENSE").write_bytes(license_source.read_bytes())


def _write_registry(target_root: Path, entries: list[dict[str, str]]) -> None:
    """Write tracing metadata for files without inline generated headers."""

    write_json(
        target_root / ".generated.json",
        registry_document(entries),
    )


def _write_copied_tree_registry(
    source_root: Path,
    target_root: Path,
    package_entries: list[tuple[Path, str]],
    manifest_entries: list[dict[str, str]],
) -> None:
    """Write tracing metadata for copied files without inline headers."""

    entries = _registry_entries_for_copied_tree(source_root)
    for package_source_root, package_target_prefix in package_entries:
        entries.extend(
            _registry_entries_for_copied_tree(
                package_source_root,
                target_prefix=package_target_prefix,
            )
        )
        license_source = _package_license_source(package_source_root)
        if license_source is not None:
            entries.append(
                registry_entry(
                    f"{package_target_prefix}LICENSE",
                    license_source.relative_to(ROOT).as_posix(),
                )
            )
    entries.extend(manifest_entries)
    _write_registry(target_root, entries)


def _manifest_registry_entry(plugin: dict, harness: str) -> tuple[Path, dict[str, str]]:
    """Return the generated plugin root and registry entry for its manifest."""

    manifest_path = ROOT / plugin_manifest_path(plugin, harness)
    plugin_root = manifest_path.parent.parent
    return (
        plugin_root,
        registry_entry(
            manifest_path.relative_to(plugin_root).as_posix(),
            MARKETPLACE_SOURCE,
        ),
    )


def _package_artifacts() -> tuple[PackageArtifact, ...]:
    """Return package copy operations for generated plugin bundles."""

    return (
        (
            ROOT / "packages" / "session-memory" / "session_memory",
            ROOT / "plugins" / "codex" / "session-memory" / "_packages" / "session_memory",
            "session_memory",
        ),
        (
            ROOT / "packages" / "session-memory" / "session_memory",
            ROOT / "plugins" / "claude" / "session-memory" / "_packages" / "session_memory",
            "session_memory",
        ),
        (
            ROOT / "packages" / "quality-guard" / "quality_guard",
            ROOT / "plugins" / "codex" / "quality-guard" / "_packages" / "quality_guard",
            "quality_guard",
        ),
        (
            ROOT / "packages" / "quality-guard" / "quality_guard",
            ROOT / "plugins" / "claude" / "quality-guard" / "_packages" / "quality_guard",
            "quality_guard",
        ),
        (
            ROOT / "packages" / "deep-research-prompt-export" / "research_prompt",
            ROOT / "plugins" / "codex" / "deep-research-prompt-export" / "_packages" / "research_prompt",
            "research_prompt",
        ),
        (
            ROOT / "packages" / "deep-research-prompt-export" / "research_prompt",
            ROOT / "plugins" / "claude" / "deep-research-prompt-export" / "_packages" / "research_prompt",
            "research_prompt",
        ),
        (
            ROOT / "packages" / "vendor" / "tomli" / "tomli",
            ROOT / "plugins" / "codex" / "session-memory" / "_packages" / "tomli",
            "tomli",
        ),
        (
            ROOT / "packages" / "vendor" / "tomli" / "tomli",
            ROOT / "plugins" / "claude" / "session-memory" / "_packages" / "tomli",
            "tomli",
        ),
        (
            ROOT / "packages" / "vendor" / "tomli" / "tomli",
            ROOT / "plugins" / "codex" / "deep-research-prompt-export" / "_packages" / "tomli",
            "tomli",
        ),
        (
            ROOT / "packages" / "vendor" / "tomli" / "tomli",
            ROOT / "plugins" / "claude" / "deep-research-prompt-export" / "_packages" / "tomli",
            "tomli",
        ),
    )


def _package_artifacts_by_target_root(
    package_artifacts: tuple[PackageArtifact, ...],
) -> dict[Path, list[tuple[Path, str]]]:
    """Group package registry sources by generated plugin root."""

    artifacts_by_target_root: dict[Path, list[tuple[Path, str]]] = {}
    for source_root, target_root, package_name in package_artifacts:
        artifacts_by_target_root.setdefault(target_root.parent.parent, []).append(
            (source_root, f"_packages/{package_name}/")
        )
    return artifacts_by_target_root


def _prune_stale_generated_plugin_roots(root: Path = ROOT) -> None:
    """Remove renamed generated plugin roots before materializing current artifacts."""

    for stale_root in STALE_GENERATED_PLUGIN_ROOTS:
        target = root / stale_root
        if target.exists():
            shutil.rmtree(target)


def main() -> int:
    """Build generated plugin marketplace artifacts."""

    _prune_stale_generated_plugin_roots(ROOT)
    metadata = load_marketplace(ROOT / "plugin-sources/marketplace.yaml")
    shared_skills_source = ROOT / "plugin-sources" / "shared-skills"
    shared_subagents_source = ROOT / "plugin-sources" / "shared-subagents"
    harness_foundry_source = ROOT / "plugin-sources" / "harness-foundry"
    session_memory_artifacts = (
        (
            ROOT / "plugin-sources" / "session-memory" / "adapters" / "codex",
            ROOT / "plugins" / "codex" / "session-memory",
        ),
        (
            ROOT / "plugin-sources" / "session-memory" / "adapters" / "claude",
            ROOT / "plugins" / "claude" / "session-memory",
        ),
    )
    quality_guard_artifacts = (
        (
            ROOT / "plugin-sources" / "quality-guard" / "adapters" / "codex",
            ROOT / "plugins" / "codex" / "quality-guard",
        ),
        (
            ROOT / "plugin-sources" / "quality-guard" / "adapters" / "claude",
            ROOT / "plugins" / "claude" / "quality-guard",
        ),
    )
    deep_research_prompt_export_artifacts = (
        (
            ROOT / "plugin-sources" / "deep-research-prompt-export" / "adapters" / "codex",
            ROOT / "plugins" / "codex" / "deep-research-prompt-export",
        ),
        (
            ROOT / "plugin-sources" / "deep-research-prompt-export" / "adapters" / "claude",
            ROOT / "plugins" / "claude" / "deep-research-prompt-export",
        ),
    )
    package_artifacts = _package_artifacts()
    copied_tree_artifacts = (
        session_memory_artifacts
        + quality_guard_artifacts
        + deep_research_prompt_export_artifacts
    )
    write_json(ROOT / ".agents/plugins/marketplace.json", render_codex_marketplace(metadata))
    write_json(ROOT / ".claude-plugin/marketplace.json", render_claude_marketplace(metadata))
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "codex" / "shared-skills",
        render_codex_skill_tree(shared_skills_source),
    )
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "claude" / "shared-skills",
        render_claude_skill_tree(shared_skills_source),
    )
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "codex" / "shared-subagents",
        render_codex_agent_tree(shared_subagents_source),
    )
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "claude" / "shared-subagents",
        render_claude_agent_tree(shared_subagents_source),
    )
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "codex" / "harness-foundry",
        render_plugin_text_tree(harness_foundry_source),
    )
    write_text_tree(
        ROOT,
        ROOT / "plugins" / "claude" / "harness-foundry",
        render_plugin_text_tree(harness_foundry_source),
    )
    for source_root, target_root in copied_tree_artifacts:
        replace_tree(ROOT, source_root, target_root)
    for source_root, target_root, _package_name in package_artifacts:
        replace_tree(ROOT, source_root, target_root)
        _copy_package_license(source_root, target_root)

    manifest_entries_by_target_root: dict[Path, list[dict[str, str]]] = {}
    for plugin in metadata["plugins"]:
        harnesses = plugin["harnesses"]
        if "codex" in harnesses:
            manifest_path = ROOT / plugin_manifest_path(plugin, "codex")
            write_json(manifest_path, render_codex_manifest(plugin))
            plugin_root, entry = _manifest_registry_entry(plugin, "codex")
            manifest_entries_by_target_root.setdefault(plugin_root, []).append(entry)
        if "claude" in harnesses:
            manifest_path = ROOT / plugin_manifest_path(plugin, "claude")
            write_json(manifest_path, render_claude_manifest(plugin))
            plugin_root, entry = _manifest_registry_entry(plugin, "claude")
            manifest_entries_by_target_root.setdefault(plugin_root, []).append(entry)
    package_artifacts_by_target_root = _package_artifacts_by_target_root(package_artifacts)
    for source_root, target_root in copied_tree_artifacts:
        _write_copied_tree_registry(
            source_root,
            target_root,
            package_artifacts_by_target_root[target_root],
            manifest_entries_by_target_root.pop(target_root, []),
        )
    for target_root, entries in manifest_entries_by_target_root.items():
        _write_registry(target_root, entries)

    print("built plugin artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
