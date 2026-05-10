from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MARKETPLACE_TARGETS = (
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
)

CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _append_string_error(
    errors: list[str],
    relative_path: Path,
    data: dict[str, Any],
    field: str,
) -> None:
    if not _is_non_empty_string(data.get(field)):
        errors.append(f"{relative_path} must have string {field}")


def _append_object_error(
    errors: list[str],
    relative_path: Path,
    data: dict[str, Any],
    field: str,
) -> dict[str, Any] | None:
    value = data.get(field)
    if not isinstance(value, dict):
        errors.append(f"{relative_path} must have object {field}")
        return None

    return value


def _append_plugins_error(
    errors: list[str],
    relative_path: Path,
    data: dict[str, Any],
) -> list[Any] | None:
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{relative_path} must have non-empty list plugins")
        return None

    return plugins


def _validate_codex_marketplace(
    relative_path: Path,
    data: dict[str, Any],
    errors: list[str],
) -> None:
    _append_string_error(errors, relative_path, data, "name")
    if data.get("name") != "engine":
        errors.append(f"{relative_path} must have name engine")

    interface = _append_object_error(errors, relative_path, data, "interface")
    if interface is not None and not _is_non_empty_string(interface.get("displayName")):
        errors.append(f"{relative_path} must have string interface.displayName")

    plugins = _append_plugins_error(errors, relative_path, data)
    if plugins is None:
        return

    for index, plugin in enumerate(plugins):
        plugin_path = f"plugins[{index}]"
        if not isinstance(plugin, dict):
            errors.append(f"{relative_path} must have object {plugin_path}")
            continue

        if not _is_non_empty_string(plugin.get("name")):
            errors.append(f"{relative_path} must have string {plugin_path}.name")

        source = plugin.get("source")
        if not isinstance(source, dict):
            errors.append(f"{relative_path} must have object {plugin_path}.source")
        else:
            if source.get("source") != "local":
                errors.append(f"{relative_path} must have {plugin_path}.source.source local")
            if not _is_non_empty_string(source.get("path")):
                errors.append(f"{relative_path} must have string {plugin_path}.source.path")

        policy = plugin.get("policy")
        if not isinstance(policy, dict):
            errors.append(f"{relative_path} must have object {plugin_path}.policy")
        else:
            if not _is_non_empty_string(policy.get("installation")):
                errors.append(f"{relative_path} must have string {plugin_path}.policy.installation")
            if not _is_non_empty_string(policy.get("authentication")):
                errors.append(f"{relative_path} must have string {plugin_path}.policy.authentication")

        if not _is_non_empty_string(plugin.get("category")):
            errors.append(f"{relative_path} must have string {plugin_path}.category")


def _validate_claude_marketplace(
    relative_path: Path,
    data: dict[str, Any],
    errors: list[str],
) -> None:
    _append_string_error(errors, relative_path, data, "$schema")
    _append_string_error(errors, relative_path, data, "name")
    if data.get("name") != "engine":
        errors.append(f"{relative_path} must have name engine")
    _append_string_error(errors, relative_path, data, "description")

    owner = _append_object_error(errors, relative_path, data, "owner")
    if owner is not None and not _is_non_empty_string(owner.get("name")):
        errors.append(f"{relative_path} must have string owner.name")

    plugins = _append_plugins_error(errors, relative_path, data)
    if plugins is None:
        return

    for index, plugin in enumerate(plugins):
        plugin_path = f"plugins[{index}]"
        if not isinstance(plugin, dict):
            errors.append(f"{relative_path} must have object {plugin_path}")
            continue

        for field in ("name", "description", "source"):
            if not _is_non_empty_string(plugin.get(field)):
                errors.append(f"{relative_path} must have string {plugin_path}.{field}")


def validate_marketplaces(root: Path) -> list[str]:
    """Validate generated marketplace files required by the build entrypoint."""

    errors: list[str] = []

    for relative_path in MARKETPLACE_TARGETS:
        path = root / relative_path
        if not path.exists():
            errors.append(f"missing generated marketplace: {relative_path}")
            continue

        try:
            data = _read_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {relative_path}: {exc.msg}")
            continue

        if not isinstance(data, dict):
            errors.append(f"generated marketplace is not an object: {relative_path}")
            continue

        if relative_path == CODEX_MARKETPLACE:
            _validate_codex_marketplace(relative_path, data, errors)
        elif relative_path == CLAUDE_MARKETPLACE:
            _validate_claude_marketplace(relative_path, data, errors)

    return errors


__all__ = ["validate_marketplaces"]
