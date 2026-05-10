from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SESSION_MEMORY_ARTIFACTS = {
    "codex": ROOT / "plugins" / "codex" / "session-memory",
    "claude": ROOT / "plugins" / "claude" / "session-memory",
}
QUALITY_GUARD_ARTIFACTS = {
    "codex": ROOT / "plugins" / "codex" / "quality-guard",
    "claude": ROOT / "plugins" / "claude" / "quality-guard",
}
RUNTIME_TEXT_SUFFIXES = frozenset({".py", ".md", ".json", ".toml"})
TRACEABLE_SUFFIXES = frozenset({".py", ".md", ".toml"})
FORBIDDEN_PACKAGE_REFERENCES = ("../packages", "../../packages")
SOURCE_TRACE_PREFIXES = {
    "quality-guard": "plugin-sources/quality-guard/adapters/",
    "session-memory": "plugin-sources/session-memory/adapters/",
}
EXPECTED_RUNTIME_FILES = {
    "quality-guard": {
        "codex": ("scripts/agents_rules.py",),
        "claude": ("hooks/hooks.json", "hooks/stop.py"),
    },
    "session-memory": {
        "codex": ("scripts/jsonl_parser.py",),
        "claude": ("commands/checkpoint.md", "hooks/hooks.json"),
    },
}


def _runtime_text_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in RUNTIME_TEXT_SUFFIXES
    )


def _traceable_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in TRACEABLE_SUFFIXES
    )


def _registry_entries(root: Path) -> list[dict[str, Any]]:
    registry_path = root / ".generated.json"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = data.get("generated")
    assert isinstance(entries, list)
    return entries


def _source_traceable_targets(plugin_name: str, harness: str) -> set[str]:
    """Return copied source files that must appear in the generated registry."""

    source_root = ROOT / "plugin-sources" / plugin_name / "adapters" / harness
    return {
        path.relative_to(source_root).as_posix()
        for path in _traceable_files(source_root)
    }


def assert_generated_registry_traces_copied_runtime_files(
    plugin_name: str,
    artifacts: dict[str, Path],
) -> None:
    """Assert copied runtime files are present and traceable to canonical sources."""

    for harness, root in artifacts.items():
        registry_targets = {
            entry["target"]: entry["source"] for entry in _registry_entries(root)
        }
        expected_targets = _source_traceable_targets(plugin_name, harness)

        assert set(registry_targets) == expected_targets
        for target, source in registry_targets.items():
            assert (root / target).is_file()
            assert source == f"{SOURCE_TRACE_PREFIXES[plugin_name]}{harness}/{target}"
            assert (root / target).read_bytes() == (ROOT / source).read_bytes()


def assert_artifact_is_self_contained(root: Path) -> None:
    """Assert that a generated artifact has no runtime source-tree references."""

    assert root.is_dir(), f"missing artifact root: {root.relative_to(ROOT)}"
    violations: list[str] = []

    for path in _runtime_text_files(root):
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_PACKAGE_REFERENCES:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)} contains {marker}")
        if "plugin-sources/" in text and path.name != ".generated.json":
            violations.append(f"{path.relative_to(ROOT)} references plugin-sources/")

    assert violations == []


def assert_artifacts_contain_expected_runtime_files(
    plugin_name: str,
    artifacts: dict[str, Path],
) -> None:
    """Assert copied artifacts retain required runtime entrypoints."""

    for harness, root in artifacts.items():
        assert root.is_dir(), f"missing artifact root: {root.relative_to(ROOT)}"
        for relative_path in EXPECTED_RUNTIME_FILES[plugin_name][harness]:
            assert (root / relative_path).is_file(), (
                f"missing runtime file: {(root / relative_path).relative_to(ROOT)}"
            )


def assert_required_runtime_json_matches_sources(
    plugin_name: str,
    artifacts: dict[str, Path],
) -> None:
    """Assert runtime-critical JSON copies stay byte-identical to sources."""

    for harness, root in artifacts.items():
        source_root = ROOT / "plugin-sources" / plugin_name / "adapters" / harness
        json_paths = (
            relative_path
            for relative_path in EXPECTED_RUNTIME_FILES[plugin_name][harness]
            if relative_path.endswith(".json")
        )
        for relative_path in json_paths:
            assert (root / relative_path).read_bytes() == (
                source_root / relative_path
            ).read_bytes()


def test_quality_guard_artifacts_are_self_contained() -> None:
    assert_artifact_is_self_contained(ROOT / "plugins/codex/quality-guard")
    assert_artifact_is_self_contained(ROOT / "plugins/claude/quality-guard")


def test_quality_guard_artifacts_contain_expected_runtime_files() -> None:
    assert_artifacts_contain_expected_runtime_files(
        "quality-guard",
        QUALITY_GUARD_ARTIFACTS,
    )


def test_quality_guard_required_runtime_json_matches_sources() -> None:
    assert_required_runtime_json_matches_sources(
        "quality-guard",
        QUALITY_GUARD_ARTIFACTS,
    )


def test_quality_guard_generated_registry_traces_copied_runtime_files() -> None:
    assert_generated_registry_traces_copied_runtime_files(
        "quality-guard",
        QUALITY_GUARD_ARTIFACTS,
    )


def test_session_memory_artifacts_contain_expected_runtime_files() -> None:
    assert_artifacts_contain_expected_runtime_files(
        "session-memory",
        SESSION_MEMORY_ARTIFACTS,
    )


def test_session_memory_required_runtime_json_matches_sources() -> None:
    assert_required_runtime_json_matches_sources(
        "session-memory",
        SESSION_MEMORY_ARTIFACTS,
    )


def test_session_memory_artifacts_do_not_reference_source_packages() -> None:
    for root in SESSION_MEMORY_ARTIFACTS.values():
        assert_artifact_is_self_contained(root)


def test_session_memory_artifacts_keep_plugin_sources_only_in_registry() -> None:
    violations: list[str] = []

    for root in SESSION_MEMORY_ARTIFACTS.values():
        for path in _runtime_text_files(root):
            if "plugin-sources/" not in path.read_text(encoding="utf-8"):
                continue
            if path.name == ".generated.json":
                continue
            violations.append(f"{path.relative_to(ROOT)} references plugin-sources/")

    assert violations == []


def test_session_memory_generated_registry_traces_copied_runtime_files() -> None:
    assert_generated_registry_traces_copied_runtime_files(
        "session-memory",
        SESSION_MEMORY_ARTIFACTS,
    )
