from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from marketplace_metadata_helpers import (
    CODEX_MANIFESTS_BY_PUBLIC_NAME,
    EXPECTED_HARNESS_PUBLIC_NAMES,
    METADATA,
    PLANNED_HARNESS_PATHS,
    minimal_marketplace_lines,
    write_metadata,
)
from tools.build.metadata import _load_marketplace_without_yaml, load_marketplace


def test_marketplace_metadata_preserves_harness_public_names() -> None:
    metadata = load_marketplace(METADATA)

    harness_public_names = {
        plugin["id"]: {
            harness: config["name"] for harness, config in plugin["harnesses"].items()
        }
        for plugin in metadata["plugins"]
    }

    assert harness_public_names == EXPECTED_HARNESS_PUBLIC_NAMES


def test_marketplace_metadata_versions_match_current_codex_manifests() -> None:
    metadata = load_marketplace(METADATA)
    manifest_versions = {
        public_name: json.loads(path.read_text(encoding="utf-8"))["version"]
        for public_name, path in CODEX_MANIFESTS_BY_PUBLIC_NAME.items()
    }

    metadata_versions = {
        plugin["harnesses"]["codex"]["name"]: plugin["version"]
        for plugin in metadata["plugins"]
    }

    assert metadata_versions == manifest_versions


def test_marketplace_metadata_harness_paths_are_planned_target_strings() -> None:
    metadata = load_marketplace(METADATA)

    harness_paths = {
        plugin["id"]: {
            harness: config["path"] for harness, config in plugin["harnesses"].items()
        }
        for plugin in metadata["plugins"]
    }

    assert harness_paths == PLANNED_HARNESS_PATHS


def test_marketplace_metadata_contains_all_target_plugin_families() -> None:
    metadata = load_marketplace(METADATA)

    plugin_ids = {plugin["id"] for plugin in metadata["plugins"]}

    assert plugin_ids == {
        "session-memory",
        "quality-guard",
        "shared-subagents",
        "shared-skills",
        "harness-foundry",
        "research-prompt",
    }


def test_load_marketplace_with_yaml_rejects_extra_keys_from_base_loader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeYaml:
        BaseLoader = object()

        @staticmethod
        def load(_text: str, *, Loader: object) -> dict[str, object]:
            assert Loader is FakeYaml.BaseLoader
            return {
                "name": "engine",
                "display_name": "Engine",
                "description": "Metadata with extra top-level data",
                "owner": {"name": "nwleedev"},
                "plugins": [],
                "homepage": "https://example.invalid",
            }

        @staticmethod
        def safe_load(_text: str) -> dict[str, object]:
            raise AssertionError("load_marketplace must use BaseLoader")

    metadata = write_metadata(tmp_path / "marketplace.yaml", ["name: ignored"])
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    with pytest.raises(ValueError, match="unsupported top-level keys: homepage"):
        load_marketplace(metadata)


@pytest.mark.parametrize(
    ("original_line", "replacement_line", "field", "expected_value"),
    [
        (
            "description: Minimal metadata",
            "description: 2024-01-01T00:00:00Z",
            ("description",),
            "2024-01-01T00:00:00Z",
        ),
        ("    version: 0.5.0", "    version: 0x10", ("plugins", 0, "version"), "0x10"),
        ("    license: MIT", "    license: 1:02", ("plugins", 0, "license"), "1:02"),
        ("    category: Productivity", "    category: .inf", ("plugins", 0, "category"), ".inf"),
        (
            "        path: ./plugins/codex/session-memory",
            "        path: .nan",
            ("plugins", 0, "harnesses", "codex", "path"),
            ".nan",
        ),
    ],
)
def test_load_marketplace_preserves_implicit_typed_scalars_as_strings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    original_line: str,
    replacement_line: str,
    field: tuple[object, ...],
    expected_value: str,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeYaml:
        BaseLoader = object()

        @staticmethod
        def load(text: str, *, Loader: object) -> dict[str, object]:
            calls.append((text, Loader))
            assert Loader is FakeYaml.BaseLoader
            return _load_marketplace_without_yaml(metadata)

        @staticmethod
        def safe_load(_text: str) -> dict[str, object]:
            raise AssertionError("load_marketplace must use BaseLoader")

    lines = minimal_marketplace_lines()
    lines[lines.index(original_line)] = replacement_line
    metadata = write_metadata(tmp_path / "marketplace.yaml", lines)
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    loaded_with_yaml = load_marketplace(metadata)
    loaded_without_yaml = _load_marketplace_without_yaml(metadata)
    value: object = loaded_with_yaml
    for key in field:
        value = value[key]  # type: ignore[index]

    assert calls == [(metadata.read_text(encoding="utf-8"), FakeYaml.BaseLoader)]
    assert value == expected_value
    assert loaded_with_yaml == loaded_without_yaml


def test_load_marketplace_without_yaml_matches_canonical_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = load_marketplace(METADATA)
    monkeypatch.setitem(sys.modules, "yaml", None)

    assert _load_marketplace_without_yaml(METADATA) == canonical
    assert load_marketplace(METADATA) == canonical
