from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SESSION_MEMORY_ARTIFACTS = {
    "codex": ROOT / "plugins" / "codex" / "session-memory",
    "claude": ROOT / "plugins" / "claude" / "session-memory",
}
RUNTIME_TEXT_SUFFIXES = frozenset({".py", ".md", ".json", ".toml"})
TRACEABLE_SUFFIXES = frozenset({".py", ".md", ".toml"})
FORBIDDEN_PACKAGE_REFERENCES = ("../packages", "../../packages")
SOURCE_TRACE_PREFIX = "plugin-sources/session-memory/adapters/"
EXPECTED_RUNTIME_FILES = {
    "codex": ("scripts/jsonl_parser.py",),
    "claude": ("commands/checkpoint.md",),
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


def test_session_memory_artifacts_contain_expected_runtime_files() -> None:
    for harness, root in SESSION_MEMORY_ARTIFACTS.items():
        assert root.is_dir(), f"missing artifact root: {root.relative_to(ROOT)}"
        for relative_path in EXPECTED_RUNTIME_FILES[harness]:
            assert (root / relative_path).is_file(), (
                f"missing runtime file: {(root / relative_path).relative_to(ROOT)}"
            )


def test_session_memory_artifacts_do_not_reference_source_packages() -> None:
    violations: list[str] = []

    for root in SESSION_MEMORY_ARTIFACTS.values():
        for path in _runtime_text_files(root):
            text = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_PACKAGE_REFERENCES:
                if marker in text:
                    violations.append(f"{path.relative_to(ROOT)} contains {marker}")

    assert violations == []


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
    for harness, root in SESSION_MEMORY_ARTIFACTS.items():
        registry_targets = {
            entry["target"]: entry["source"] for entry in _registry_entries(root)
        }
        expected_targets = {
            path.relative_to(root).as_posix() for path in _traceable_files(root)
        }

        assert set(registry_targets) == expected_targets
        for target, source in registry_targets.items():
            assert source == f"{SOURCE_TRACE_PREFIX}{harness}/{target}"
