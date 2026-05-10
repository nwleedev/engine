from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.build.paths import normalize_harness_path


TOP_LEVEL_REQUIRED_KEYS = {"name", "display_name", "description", "owner", "plugins"}
TOP_LEVEL_ALLOWED_KEYS = TOP_LEVEL_REQUIRED_KEYS
TOP_LEVEL_SCALAR_KEYS = ("name", "display_name", "description")
OWNER_REQUIRED_KEYS = {"name"}
OWNER_ALLOWED_KEYS = OWNER_REQUIRED_KEYS
PLUGIN_REQUIRED_KEYS = {
    "id",
    "version",
    "description",
    "license",
    "category",
    "harnesses",
}
PLUGIN_ALLOWED_KEYS = PLUGIN_REQUIRED_KEYS
PLUGIN_SCALAR_KEYS = ("id", "version", "description", "license", "category")
HARNESS_REQUIRED_KEYS = {"name", "path"}
HARNESS_ALLOWED_KEYS = {"name", "path", "skills"}
HARNESS_SCALAR_KEYS = ("name", "skills", "path")


def _validate_marketplace_metadata(data: Any, path: Path) -> dict[str, Any]:
    """Validate the canonical marketplace metadata shape used by build tooling."""

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    _require_string_keys(data, f"{path} top-level")

    extra_top_level = data.keys() - TOP_LEVEL_ALLOWED_KEYS
    if extra_top_level:
        extra = ", ".join(sorted(extra_top_level))
        raise ValueError(f"{path} has unsupported top-level keys: {extra}")

    missing_top_level = TOP_LEVEL_REQUIRED_KEYS - data.keys()
    if missing_top_level:
        missing = ", ".join(sorted(missing_top_level))
        raise ValueError(f"{path} is missing required top-level keys: {missing}")

    for key in TOP_LEVEL_SCALAR_KEYS:
        _require_string_scalar(data[key], f"{path} top-level {key}")

    _validate_owner_metadata(data, path)
    _validate_plugin_metadata(data, path)

    json.dumps(data)
    return data


def _validate_owner_metadata(data: dict[Any, Any], path: Path) -> None:
    """Validate marketplace owner metadata."""

    if not isinstance(data["owner"], dict):
        raise ValueError(f"{path} owner must be a mapping")
    _require_string_keys(data["owner"], f"{path} owner")
    extra_owner = data["owner"].keys() - OWNER_ALLOWED_KEYS
    if extra_owner:
        extra = ", ".join(sorted(extra_owner))
        raise ValueError(f"{path} owner has unsupported keys: {extra}")
    missing_owner = OWNER_REQUIRED_KEYS - data["owner"].keys()
    if missing_owner:
        missing = ", ".join(sorted(missing_owner))
        raise ValueError(f"{path} owner is missing required keys: {missing}")
    _require_string_scalar(data["owner"]["name"], f"{path} owner.name")


def _validate_plugin_metadata(data: dict[Any, Any], path: Path) -> None:
    """Validate all plugin entries and their nested harness metadata."""

    if not isinstance(data["plugins"], list):
        raise ValueError(f"{path} plugins must be a list")

    plugin_ids: set[str] = set()
    harness_public_names: set[tuple[str, str]] = set()

    for index, plugin in enumerate(data["plugins"]):
        if not isinstance(plugin, dict):
            raise ValueError(f"{path} plugin #{index + 1} must be a mapping")

        plugin_id = plugin.get("id", f"#{index + 1}")
        plugin_context = (
            f"{path} plugin {plugin_id}"
            if isinstance(plugin_id, str)
            else f"{path} plugin #{index + 1}"
        )
        _validate_plugin_keys(plugin, plugin_context)

        for key in PLUGIN_SCALAR_KEYS:
            _require_string_scalar(plugin[key], f"{plugin_context}.{key}")

        if plugin["id"] in plugin_ids:
            raise ValueError(f"{path} has duplicate plugin id: {plugin['id']}")
        plugin_ids.add(plugin["id"])

        _validate_plugin_harnesses(plugin, path, harness_public_names)


def _validate_plugin_keys(plugin: dict[Any, Any], plugin_context: str) -> None:
    """Validate plugin mapping keys before reading required scalar values."""

    _require_string_keys(plugin, plugin_context)

    extra_plugin = plugin.keys() - PLUGIN_ALLOWED_KEYS
    if extra_plugin:
        extra = ", ".join(sorted(extra_plugin))
        raise ValueError(f"{plugin_context} has unsupported keys: {extra}")

    missing_plugin = PLUGIN_REQUIRED_KEYS - plugin.keys()
    if missing_plugin:
        missing = ", ".join(sorted(missing_plugin))
        raise ValueError(f"{plugin_context} is missing keys: {missing}")


def _validate_plugin_harnesses(
    plugin: dict[Any, Any],
    path: Path,
    harness_public_names: set[tuple[str, str]],
) -> None:
    """Validate harness mappings for a single plugin."""

    harnesses = plugin["harnesses"]
    if not isinstance(harnesses, dict):
        raise ValueError(f"{path} plugin {plugin['id']} harnesses must be a mapping")

    for harness_name, harness in harnesses.items():
        if not isinstance(harness_name, str):
            raise ValueError(
                f"{path} plugin {plugin['id']} harness key {harness_name} "
                "must be a string"
            )
        _validate_harness_metadata(plugin, harness_name, harness, path)
        harness_public_name = (harness_name, harness["name"])
        if harness_public_name in harness_public_names:
            raise ValueError(f"{path} has duplicate harness public name: {harness['name']}")
        harness_public_names.add(harness_public_name)


def _validate_harness_metadata(
    plugin: dict[Any, Any],
    harness_name: str,
    harness: Any,
    path: Path,
) -> None:
    """Validate a single harness metadata mapping."""

    if not isinstance(harness, dict):
        raise ValueError(
            f"{path} plugin {plugin['id']} harness {harness_name} must be a mapping"
        )
    _require_string_keys(harness, f"{path} plugin {plugin['id']} harness {harness_name}")
    extra_harness = harness.keys() - HARNESS_ALLOWED_KEYS
    if extra_harness:
        extra = ", ".join(sorted(extra_harness))
        raise ValueError(
            f"{path} plugin {plugin['id']} harness {harness_name} "
            f"has unsupported keys: {extra}"
        )
    missing_harness = HARNESS_REQUIRED_KEYS - harness.keys()
    if missing_harness:
        missing = ", ".join(sorted(missing_harness))
        raise ValueError(
            f"{path} plugin {plugin['id']} harness {harness_name} "
            f"is missing keys: {missing}"
        )
    for key in HARNESS_SCALAR_KEYS:
        if key in harness:
            _require_string_scalar(
                harness[key],
                f"{path} plugin {plugin['id']} harness {harness_name}.{key}",
            )
    normalize_harness_path(harness["path"])


def _require_string_scalar(value: Any, context: str) -> None:
    """Reject YAML scalar types that are not canonical string values."""

    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")


def _require_string_keys(mapping: dict[Any, Any], context: str) -> None:
    """Reject PyYAML mapping keys that are not canonical string keys."""

    for key in mapping:
        if not isinstance(key, str):
            raise ValueError(f"{context} key {key} must be a string")
