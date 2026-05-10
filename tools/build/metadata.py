from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.build.metadata_parser import (
    _load_marketplace_without_yaml,
    _parse_marketplace_without_yaml,
    _preflight_marketplace_text,
)
from tools.build.metadata_validator import _validate_marketplace_metadata


def load_marketplace(path: Path) -> dict[str, Any]:
    """Load the canonical marketplace metadata.

    The file uses a small YAML subset so the build does not need a runtime
    dependency. The parser intentionally supports only mappings, lists, and
    scalar strings used by `plugin-sources/marketplace.yaml`.
    """

    text = path.read_text(encoding="utf-8")
    _preflight_marketplace_text(path, text)

    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return _parse_marketplace_without_yaml(path, text)

    try:
        data = yaml.load(text, Loader=yaml.BaseLoader)
    except Exception as exc:
        raise ValueError(f"{path} could not be parsed as YAML") from exc

    return _validate_marketplace_metadata(data, path)


__all__ = [
    "_load_marketplace_without_yaml",
    "_parse_marketplace_without_yaml",
    "_preflight_marketplace_text",
    "_validate_marketplace_metadata",
    "load_marketplace",
]
