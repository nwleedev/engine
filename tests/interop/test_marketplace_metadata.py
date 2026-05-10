from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
# pytest importlib mode does not add the project root for this interop import.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.metadata import (
    _load_marketplace_without_yaml,
    _validate_marketplace_metadata,
    load_marketplace,
)


METADATA = ROOT / "plugin-sources" / "marketplace.yaml"
CODEX_MANIFESTS_BY_PUBLIC_NAME = {
    "codex-session-memory": ROOT
    / "plugins"
    / "codex-session-memory"
    / ".codex-plugin"
    / "plugin.json",
    "codex-quality-guard": ROOT
    / "plugins"
    / "codex-quality-guard"
    / ".codex-plugin"
    / "plugin.json",
    "shared-subagents": ROOT
    / "plugins"
    / "shared-subagents"
    / ".codex-plugin"
    / "plugin.json",
    "shared-skills": ROOT
    / "plugins"
    / "shared-skills"
    / ".codex-plugin"
    / "plugin.json",
    "harness-foundry": ROOT
    / "plugins"
    / "harness-foundry"
    / ".codex-plugin"
    / "plugin.json",
}
PLANNED_HARNESS_PATHS = {
    "session-memory": {
        "claude": "./plugins/claude/session-memory",
        "codex": "./plugins/codex/session-memory",
    },
    "quality-guard": {
        "claude": "./plugins/claude/quality-guard",
        "codex": "./plugins/codex/quality-guard",
    },
    "shared-subagents": {
        "claude": "./plugins/claude/shared-subagents",
        "codex": "./plugins/codex/shared-subagents",
    },
    "shared-skills": {
        "claude": "./plugins/claude/shared-skills",
        "codex": "./plugins/codex/shared-skills",
    },
    "harness-foundry": {
        "claude": "./plugins/claude/harness-foundry",
        "codex": "./plugins/codex/harness-foundry",
    },
}
EXPECTED_HARNESS_PUBLIC_NAMES = {
    "session-memory": {
        "claude": "session-memory",
        "codex": "codex-session-memory",
    },
    "quality-guard": {
        "claude": "quality-guard",
        "codex": "codex-quality-guard",
    },
    "shared-subagents": {
        "claude": "shared-subagents",
        "codex": "shared-subagents",
    },
    "shared-skills": {
        "claude": "shared-skills",
        "codex": "shared-skills",
    },
    "harness-foundry": {
        "claude": "harness-foundry",
        "codex": "harness-foundry",
    },
}


def _minimal_marketplace_metadata() -> dict[object, object]:
    return {
        "name": "engine",
        "display_name": "Engine",
        "description": "Minimal metadata",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            }
        ],
    }


def test_marketplace_metadata_preserves_harness_public_names() -> None:
    metadata = load_marketplace(METADATA)

    harness_public_names = {
        plugin["id"]: {
            harness: config["name"]
            for harness, config in plugin["harnesses"].items()
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
            harness: config["path"]
            for harness, config in plugin["harnesses"].items()
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
    }


def test_load_marketplace_without_yaml_rejects_missing_plugins_key(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata without plugin declarations",
                "owner:",
                "  name: nwleedev",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="plugins"):
        _load_marketplace_without_yaml(metadata)


def test_load_marketplace_without_yaml_rejects_unknown_unsupported_line(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with unsupported input",
                "owner:",
                "  name: nwleedev",
                "plugins:",
                "  unsupported: value",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported line"):
        _load_marketplace_without_yaml(metadata)


def test_load_marketplace_without_yaml_rejects_inline_scalar_comments(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with inline comments",
                "owner:",
                "  name: nwleedev",
                "plugins:",
                "  - id: session-memory",
                "    version: 0.4.0 # comment",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Inline comments"):
        _load_marketplace_without_yaml(metadata)


def test_validate_marketplace_metadata_rejects_missing_plugin_key(tmp_path: Path) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata without plugin version",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="version"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_duplicate_plugin_ids(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with duplicate plugin ids",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            },
            {
                "id": "session-memory",
                "version": "0.4.1",
                "description": "Duplicate family entry",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory-v2",
                        "path": "./plugins/codex/session-memory-v2",
                    }
                },
            },
        ],
    }

    with pytest.raises(ValueError, match="duplicate plugin id"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_duplicate_harness_public_names(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with duplicate harness public names",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            },
            {
                "id": "quality-guard",
                "version": "0.1.0",
                "description": "Quality diagnostics for Codex workflows",
                "license": "MIT",
                "category": "Quality",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/quality-guard",
                    }
                },
            },
        ],
    }

    with pytest.raises(ValueError, match="duplicate harness public name"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_allows_same_family_public_name_across_harnesses(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with shared generated artifact family names",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "shared-skills",
                "version": "0.2.4",
                "description": "Shared skills for multiple harnesses",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "claude": {
                        "name": "shared-skills",
                        "path": "./plugins/claude/shared-skills",
                    },
                    "codex": {
                        "name": "shared-skills",
                        "path": "./plugins/codex/shared-skills",
                    },
                },
            }
        ],
    }

    assert (
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")
        == metadata
    )


def test_validate_marketplace_metadata_rejects_extra_top_level_key(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with extra top-level data",
        "owner": {"name": "nwleedev"},
        "plugins": [],
        "homepage": "https://example.invalid",
    }

    with pytest.raises(ValueError, match="unsupported top-level keys: homepage"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_extra_plugin_key(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with extra plugin data",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
                "homepage": "https://example.invalid",
            }
        ],
    }

    with pytest.raises(ValueError, match="unsupported keys: homepage"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_missing_harness_key(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata without harness path",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                    }
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="path"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_extra_harness_key(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with extra harness data",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": "0.4.0",
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                        "homepage": "https://example.invalid",
                    }
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="unsupported keys: homepage"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_missing_owner_name(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata without owner name",
        "owner": {},
        "plugins": [],
    }

    with pytest.raises(ValueError, match="owner"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_typed_scalars_from_yaml(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": 123,
        "display_name": "Engine",
        "description": "Metadata with typed scalars",
        "owner": {"name": "nwleedev"},
        "plugins": [
            {
                "id": "session-memory",
                "version": 0.4,
                "description": "Automatic session context narration and injection",
                "license": "MIT",
                "category": "Productivity",
                "harnesses": {
                    "codex": {
                        "name": "codex-session-memory",
                        "path": "./plugins/codex/session-memory",
                    }
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="name"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


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

    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text("name: ignored\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    with pytest.raises(ValueError, match="unsupported top-level keys: homepage"):
        load_marketplace(metadata)


def test_validate_marketplace_metadata_rejects_non_string_extra_top_level_key(
    tmp_path: Path,
) -> None:
    metadata = _minimal_marketplace_metadata()
    metadata[1] = "bad"

    with pytest.raises(ValueError, match="top-level key 1 must be a string"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_non_string_extra_plugin_key(
    tmp_path: Path,
) -> None:
    metadata = _minimal_marketplace_metadata()
    plugin = metadata["plugins"][0]
    plugin[1] = "bad"

    with pytest.raises(ValueError, match="plugin session-memory key 1 must be a string"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_non_string_extra_harness_key(
    tmp_path: Path,
) -> None:
    metadata = _minimal_marketplace_metadata()
    harness = metadata["plugins"][0]["harnesses"]["codex"]
    harness[1] = "bad"

    with pytest.raises(
        ValueError,
        match="plugin session-memory harness codex key 1 must be a string",
    ):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_non_string_harness_name_key(
    tmp_path: Path,
) -> None:
    metadata = _minimal_marketplace_metadata()
    harnesses = metadata["plugins"][0]["harnesses"]
    harnesses[True] = {
        "name": "codex-session-memory",
        "path": "./plugins/codex/session-memory",
    }

    with pytest.raises(
        ValueError,
        match="plugin session-memory harness key True must be a string",
    ):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("description", True),
        ("version", 1),
        ("version", 1.0),
    ],
)
def test_validate_marketplace_metadata_rejects_typed_string_fields(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    metadata = _minimal_marketplace_metadata()
    if field == "description":
        metadata[field] = value
    else:
        metadata["plugins"][0][field] = value

    with pytest.raises(ValueError, match=f"{field} must be a string"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


@pytest.mark.parametrize(("field", "value"), [("path", True), ("path", 1)])
def test_validate_marketplace_metadata_rejects_typed_harness_string_fields(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    metadata = _minimal_marketplace_metadata()
    metadata["plugins"][0]["harnesses"]["codex"][field] = value

    with pytest.raises(ValueError, match=f"{field} must be a string"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_load_marketplace_rejects_inline_comments_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with inline comments",
                "owner:",
                "  name: nwleedev",
                "plugins:",
                "  - id: session-memory",
                "    version: 0.4.0 # comment",
                "    description: Automatic session context narration and injection",
                "    license: MIT",
                "    category: Productivity",
                "    harnesses:",
                "      codex:",
                "        name: codex-session-memory",
                "        path: ./plugins/codex/session-memory",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Inline comments"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_comment_only_lines_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "  # top comment",
                "description: Metadata with a comment-only line",
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="comments"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_tabs_before_parsing(tmp_path: Path) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with tab indentation",
                "owner:",
                "\tname: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tabs"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_document_markers_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "---",
                "name: engine",
                "display_name: Engine",
                "description: Metadata with a document marker",
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="document markers"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_directives_before_parsing(tmp_path: Path) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "%YAML 1.2",
                "name: engine",
                "display_name: Engine",
                "description: Metadata with a directive",
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directives"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_block_scalars_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: |",
                "  Metadata with a block scalar",
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="block scalar"):
        load_marketplace(metadata)


@pytest.mark.parametrize("value", ["&desc Metadata", "*desc", "<<: *defaults"])
def test_load_marketplace_rejects_anchors_aliases_or_merge_before_parsing(
    tmp_path: Path,
    value: str,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                f"description: {value}",
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="anchors, aliases, and merge keys"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_unsupported_indentation_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with unsupported indentation",
                "owner:",
                "   name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="indentation"):
        load_marketplace(metadata)


@pytest.mark.parametrize(
    ("original_line", "replacement_line"),
    [
        ("name: engine", "name:  engine"),
        ("    version: 0.4.0", "    version:  0.4.0"),
        (
            "        path: ./plugins/codex/session-memory",
            "        path:  ./plugins/codex/session-memory",
        ),
    ],
)
def test_load_marketplace_rejects_extra_spaces_after_mapping_separator(
    tmp_path: Path,
    original_line: str,
    replacement_line: str,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    lines = [
        "name: engine",
        "display_name: Engine",
        "description: Metadata with unsupported separator spacing",
        "owner:",
        "  name: nwleedev",
        "plugins:",
        "  - id: session-memory",
        "    version: 0.4.0",
        "    description: Automatic session context narration and injection",
        "    license: MIT",
        "    category: Productivity",
        "    harnesses:",
        "      codex:",
        "        name: codex-session-memory",
        "        path: ./plugins/codex/session-memory",
    ]
    lines[lines.index(original_line)] = replacement_line
    metadata.write_text("\n".join(lines), encoding="utf-8")

    with pytest.raises(ValueError, match="extra spaces"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_quoted_scalars_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                'description: "Quoted description"',
                "owner:",
                "  name: nwleedev",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="quoted"):
        load_marketplace(metadata)


@pytest.mark.parametrize(
    "value", ["!!str tagged description", "!custom tagged description"]
)
def test_load_marketplace_rejects_explicit_tags_before_parsing(
    tmp_path: Path,
    value: str,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                f"description: {value}",
                "owner:",
                "  name: nwleedev",
                "plugins:",
                "  - id: session-memory",
                "    version: 0.4.0",
                "    description: Automatic session context narration and injection",
                "    license: MIT",
                "    category: Productivity",
                "    harnesses:",
                "      codex:",
                "        name: codex-session-memory",
                "        path: ./plugins/codex/session-memory",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tags?"):
        load_marketplace(metadata)


def test_load_marketplace_rejects_inline_collections_before_parsing(
    tmp_path: Path,
) -> None:
    metadata = tmp_path / "marketplace.yaml"
    metadata.write_text(
        "\n".join(
            [
                "name: engine",
                "display_name: Engine",
                "description: Metadata with inline collections",
                "owner: {name: nwleedev}",
                "plugins:",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="inline collection"):
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
        (
            "    version: 0.4.0",
            "    version: 0x10",
            ("plugins", 0, "version"),
            "0x10",
        ),
        ("    license: MIT", "    license: 1:02", ("plugins", 0, "license"), "1:02"),
        (
            "    category: Productivity",
            "    category: .inf",
            ("plugins", 0, "category"),
            ".inf",
        ),
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

    metadata = tmp_path / "marketplace.yaml"
    lines = [
        "name: engine",
        "display_name: Engine",
        "description: Minimal metadata",
        "owner:",
        "  name: nwleedev",
        "plugins:",
        "  - id: session-memory",
        "    version: 0.4.0",
        "    description: Automatic session context narration and injection",
        "    license: MIT",
        "    category: Productivity",
        "    harnesses:",
        "      codex:",
        "        name: codex-session-memory",
        "        path: ./plugins/codex/session-memory",
    ]
    lines[lines.index(original_line)] = replacement_line
    metadata.write_text("\n".join(lines), encoding="utf-8")
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    loaded_with_yaml = load_marketplace(metadata)
    loaded_without_yaml = _load_marketplace_without_yaml(metadata)
    value: object = loaded_with_yaml
    for key in field:
        value = value[key]  # type: ignore[index]

    assert calls == [(metadata.read_text(encoding="utf-8"), FakeYaml.BaseLoader)]
    assert value == expected_value
    assert loaded_with_yaml == loaded_without_yaml


def test_validate_marketplace_metadata_rejects_extra_owner_key(
    tmp_path: Path,
) -> None:
    metadata = {
        "name": "engine",
        "display_name": "Engine",
        "description": "Metadata with extra owner data",
        "owner": {
            "name": "nwleedev",
            "email": "owner@example.invalid",
        },
        "plugins": [],
    }

    with pytest.raises(ValueError, match="owner has unsupported keys: email"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_load_marketplace_without_yaml_matches_canonical_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = load_marketplace(METADATA)
    monkeypatch.setitem(sys.modules, "yaml", None)

    assert _load_marketplace_without_yaml(METADATA) == canonical
    assert load_marketplace(METADATA) == canonical
