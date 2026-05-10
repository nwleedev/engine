from __future__ import annotations

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


COPIED_TREE_TRACEABLE_SUFFIXES = frozenset({".md", ".py", ".toml"})


def _registry_entries_for_copied_tree(
    source_root: Path,
) -> list[dict[str, str]]:
    """Return generated registry entries for raw copied adapter files."""

    return [
        registry_entry(
            source_path.relative_to(source_root).as_posix(),
            source_path.relative_to(ROOT).as_posix(),
        )
        for source_path in sorted(source_root.rglob("*"))
        if source_path.is_file()
        and source_path.suffix in COPIED_TREE_TRACEABLE_SUFFIXES
    ]


def _write_copied_tree_registry(source_root: Path, target_root: Path) -> None:
    """Write tracing metadata for copied files without inline headers."""

    write_json(
        target_root / ".generated.json",
        registry_document(_registry_entries_for_copied_tree(source_root)),
    )


def main() -> int:
    """Build generated plugin marketplace artifacts."""

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
    copied_tree_artifacts = session_memory_artifacts + quality_guard_artifacts
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

    for plugin in metadata["plugins"]:
        harnesses = plugin["harnesses"]
        if "codex" in harnesses:
            write_json(
                ROOT / plugin_manifest_path(plugin, "codex"),
                render_codex_manifest(plugin),
            )
        if "claude" in harnesses:
            write_json(
                ROOT / plugin_manifest_path(plugin, "claude"),
                render_claude_manifest(plugin),
            )
    for source_root, target_root in copied_tree_artifacts:
        _write_copied_tree_registry(source_root, target_root)

    print("built plugin artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
