from __future__ import annotations

import sys
from pathlib import Path

import pytest

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from marketplace_metadata_helpers import minimal_marketplace_metadata
from tools.build.metadata_validator import _validate_marketplace_metadata


def test_validate_marketplace_metadata_rejects_missing_plugin_key(tmp_path: Path) -> None:
    metadata = minimal_marketplace_metadata()
    del metadata["plugins"][0]["version"]

    with pytest.raises(ValueError, match="version"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_duplicate_plugin_ids(
    tmp_path: Path,
) -> None:
    metadata = minimal_marketplace_metadata()
    duplicate = minimal_marketplace_metadata()["plugins"][0]
    duplicate["version"] = "0.4.1"
    duplicate["harnesses"]["codex"]["name"] = "session-memory-v2"
    metadata["plugins"].append(duplicate)

    with pytest.raises(ValueError, match="duplicate plugin id"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_rejects_duplicate_harness_public_names(
    tmp_path: Path,
) -> None:
    metadata = minimal_marketplace_metadata()
    duplicate = minimal_marketplace_metadata()["plugins"][0]
    duplicate["id"] = "quality-guard"
    duplicate["version"] = "0.2.0"
    duplicate["harnesses"]["codex"]["path"] = "./plugins/codex/quality-guard"
    metadata["plugins"].append(duplicate)

    with pytest.raises(ValueError, match="duplicate harness public name"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


def test_validate_marketplace_metadata_allows_same_family_public_name_across_harnesses(
    tmp_path: Path,
) -> None:
    metadata = minimal_marketplace_metadata()
    metadata["plugins"][0]["id"] = "shared-skills"
    metadata["plugins"][0]["harnesses"] = {
        "claude": {"name": "shared-skills", "path": "./plugins/claude/shared-skills"},
        "codex": {"name": "shared-skills", "path": "./plugins/codex/shared-skills"},
    }

    assert _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml") == metadata


@pytest.mark.parametrize(
    ("target", "key", "message"),
    [
        ((), "homepage", "unsupported top-level keys: homepage"),
        (("plugins", 0), "homepage", "unsupported keys: homepage"),
        (("plugins", 0, "harnesses", "codex"), "homepage", "unsupported keys: homepage"),
        (("owner",), "email", "owner has unsupported keys: email"),
    ],
)
def test_validate_marketplace_metadata_rejects_extra_keys(
    tmp_path: Path,
    target: tuple[object, ...],
    key: str,
    message: str,
) -> None:
    metadata = minimal_marketplace_metadata()
    node: dict[object, object] = metadata
    for segment in target:
        node = node[segment]  # type: ignore[index,assignment]
    node[key] = "https://example.invalid"

    with pytest.raises(ValueError, match=message):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_harness_path", "path"),
        ("missing_owner_name", "owner"),
        ("typed_top_level_name", "name"),
        ("non_string_top_level_key", "top-level key 1 must be a string"),
        ("non_string_plugin_key", "plugin session-memory key 1 must be a string"),
        (
            "non_string_harness_key",
            "plugin session-memory harness codex key 1 must be a string",
        ),
        (
            "non_string_harness_name_key",
            "plugin session-memory harness key True must be a string",
        ),
    ],
)
def test_validate_marketplace_metadata_rejects_invalid_shapes(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    metadata = minimal_marketplace_metadata()
    plugin = metadata["plugins"][0]
    harness = plugin["harnesses"]["codex"]

    if mutation == "missing_harness_path":
        del harness["path"]
    elif mutation == "missing_owner_name":
        metadata["owner"] = {}
    elif mutation == "typed_top_level_name":
        metadata["name"] = 123
        plugin["version"] = 0.4
    elif mutation == "non_string_top_level_key":
        metadata[1] = "bad"
    elif mutation == "non_string_plugin_key":
        plugin[1] = "bad"
    elif mutation == "non_string_harness_key":
        harness[1] = "bad"
    elif mutation == "non_string_harness_name_key":
        plugin["harnesses"][True] = {
            "name": "session-memory",
            "path": "./plugins/codex/session-memory",
        }

    with pytest.raises(ValueError, match=message):
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
    metadata = minimal_marketplace_metadata()
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
    metadata = minimal_marketplace_metadata()
    metadata["plugins"][0]["harnesses"]["codex"][field] = value

    with pytest.raises(ValueError, match=f"{field} must be a string"):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")


@pytest.mark.parametrize(
    ("harness_name", "path_value", "message"),
    [
        ("codex", "", "harness path must not be empty"),
        ("claude", "   ", "harness path must not be empty"),
        ("codex", ".", "harness path must not point to repository root"),
        ("claude", "./", "harness path must not point to repository root"),
        ("codex", "/abs/path", "harness path must be relative"),
        ("claude", "../escape", "harness path must not escape the repository"),
    ],
)
def test_validate_marketplace_metadata_rejects_unsafe_harness_paths(
    tmp_path: Path,
    harness_name: str,
    path_value: str,
    message: str,
) -> None:
    metadata = minimal_marketplace_metadata()
    metadata["plugins"][0]["harnesses"][harness_name] = {
        "name": f"{harness_name}-session-memory",
        "path": path_value,
    }

    with pytest.raises(ValueError, match=message):
        _validate_marketplace_metadata(metadata, tmp_path / "marketplace.yaml")
