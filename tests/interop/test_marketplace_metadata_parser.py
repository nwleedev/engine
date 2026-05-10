from __future__ import annotations

import sys
from pathlib import Path

import pytest

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from marketplace_metadata_helpers import minimal_marketplace_lines, write_metadata
from tools.build.metadata_parser import _load_marketplace_without_yaml
from tools.build.metadata import load_marketplace


def test_load_marketplace_without_yaml_rejects_missing_plugins_key(
    tmp_path: Path,
) -> None:
    metadata = write_metadata(
        tmp_path / "marketplace.yaml",
        [
            "name: engine",
            "display_name: Engine",
            "description: Metadata without plugin declarations",
            "owner:",
            "  name: nwleedev",
        ],
    )

    with pytest.raises(ValueError, match="plugins"):
        _load_marketplace_without_yaml(metadata)


def test_load_marketplace_without_yaml_rejects_unknown_unsupported_line(
    tmp_path: Path,
) -> None:
    metadata = write_metadata(
        tmp_path / "marketplace.yaml",
        [
            "name: engine",
            "display_name: Engine",
            "description: Metadata with unsupported input",
            "owner:",
            "  name: nwleedev",
            "plugins:",
            "  unsupported: value",
        ],
    )

    with pytest.raises(ValueError, match="Unsupported line"):
        _load_marketplace_without_yaml(metadata)


def test_load_marketplace_without_yaml_rejects_inline_scalar_comments(
    tmp_path: Path,
) -> None:
    lines = minimal_marketplace_lines()
    lines[lines.index("    version: 0.4.0")] = "    version: 0.4.0 # comment"
    metadata = write_metadata(tmp_path / "marketplace.yaml", lines)

    with pytest.raises(ValueError, match="Inline comments"):
        _load_marketplace_without_yaml(metadata)


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (["name: engine", "display_name: Engine", "  # top comment"], "comments"),
        (["name: engine", "owner:", "\tname: nwleedev", "plugins:"], "tabs"),
        (["---", "name: engine", "plugins:"], "document markers"),
        (["%YAML 1.2", "name: engine", "plugins:"], "directives"),
        (["name: engine", "description: |", "  Metadata", "plugins:"], "block scalar"),
        (["name: engine", "description: &desc Metadata", "plugins:"], "anchors"),
        (["name: engine", "owner:", "   name: nwleedev", "plugins:"], "indentation"),
        (["name:  engine", "plugins:"], "extra spaces"),
        (["name: engine", 'description: "Quoted"', "plugins:"], "quoted"),
        (["name: engine", "description: !custom tagged", "plugins:"], "tags?"),
        (["name: engine", "owner: {name: nwleedev}", "plugins:"], "inline collection"),
    ],
)
def test_load_marketplace_rejects_unsupported_yaml_before_parsing(
    tmp_path: Path,
    lines: list[str],
    message: str,
) -> None:
    metadata = write_metadata(tmp_path / "marketplace.yaml", lines)

    with pytest.raises(ValueError, match=message):
        load_marketplace(metadata)


@pytest.mark.parametrize("value", ["*desc", "<<: *defaults"])
def test_load_marketplace_rejects_aliases_or_merge_before_parsing(
    tmp_path: Path,
    value: str,
) -> None:
    metadata = write_metadata(
        tmp_path / "marketplace.yaml",
        ["name: engine", f"description: {value}", "plugins:"],
    )

    with pytest.raises(ValueError, match="anchors, aliases, and merge keys"):
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
    lines = minimal_marketplace_lines()
    lines[lines.index(original_line)] = replacement_line
    metadata = write_metadata(tmp_path / "marketplace.yaml", lines)

    with pytest.raises(ValueError, match="extra spaces"):
        load_marketplace(metadata)
