from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
SUPPORTED_INDENT_LEVELS = {0, 2, 4, 6, 8}
BLOCK_SCALAR_VALUES = {"|", ">", "|-", ">-", "|+", ">+"}


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


def _load_marketplace_without_yaml(path: Path) -> dict[str, Any]:
    """Parse the current marketplace YAML subset without external packages."""

    text = path.read_text(encoding="utf-8")
    _preflight_marketplace_text(path, text)
    return _parse_marketplace_without_yaml(path, text)


def _preflight_marketplace_text(path: Path, text: str) -> None:
    """Reject YAML syntax that would make optional parser paths diverge."""

    if "\t" in text:
        raise ValueError(f"{path} must use spaces, not tabs")
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped:
            continue

        leading_spaces = len(line) - len(line.lstrip(" "))
        if leading_spaces not in SUPPORTED_INDENT_LEVELS:
            raise ValueError(
                f"unsupported indentation in {path}:{line_number}; use 0, 2, 4, "
                "6, or 8 leading spaces"
            )
        if stripped.startswith("#"):
            raise ValueError(f"YAML comments are not supported in {path}:{line_number}")
        if stripped in {"---", "..."}:
            raise ValueError(
                f"YAML document markers are not supported in {path}:{line_number}"
            )
        if stripped.startswith("%"):
            raise ValueError(f"YAML directives are not supported in {path}:{line_number}")
        if " #" in line:
            raise ValueError(f"Inline comments are not supported in {path}:{line_number}")
        if ": " in line:
            raw_value = line.split(": ", 1)[1]
            if raw_value.startswith(" "):
                raise ValueError(
                    "extra spaces after mapping separator are not supported in "
                    f"{path}:{line_number}"
                )
            value = raw_value.strip()
            if value in BLOCK_SCALAR_VALUES:
                raise ValueError(
                    f"block scalar values are not supported in {path}:{line_number}"
                )
            if value.startswith(("&", "*", "<<")):
                raise ValueError(
                    "YAML anchors, aliases, and merge keys are not supported in "
                    f"{path}:{line_number}"
                )
            if value.startswith("!"):
                raise ValueError(
                    f"YAML tags are not supported in {path}:{line_number}"
                )
            if value.startswith(("'", '"')):
                raise ValueError(
                    f"quoted scalar values are not supported in {path}:{line_number}"
                )
            if value.startswith(("[", "{")):
                raise ValueError(
                    f"inline collection values are not supported in "
                    f"{path}:{line_number}"
                )


def _parse_marketplace_without_yaml(path: Path, text: str) -> dict[str, Any]:
    """Parse the current marketplace YAML subset without external packages."""

    # Convert the known canonical metadata through a conservative line parser.
    result: dict[str, Any] = {}
    current_plugin: dict[str, Any] | None = None
    current_harness: str | None = None
    plugins_seen = False
    harnesses_seen = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("name: "):
            result["name"] = _scalar_value(path, line_number, line, "name: ")
        elif line.startswith("display_name: "):
            result["display_name"] = _scalar_value(
                path, line_number, line, "display_name: "
            )
        elif line.startswith("description: "):
            result["description"] = _scalar_value(
                path, line_number, line, "description: "
            )
        elif line == "owner:":
            result["owner"] = {}
        elif line.startswith("  name: ") and isinstance(result.get("owner"), dict):
            result["owner"]["name"] = _scalar_value(path, line_number, line, "  name: ")
        elif line == "plugins:":
            result["plugins"] = []
            plugins_seen = True
            current_plugin = None
            current_harness = None
            harnesses_seen = False
        elif line.startswith("  - id: "):
            if not plugins_seen:
                raise ValueError(f"{path}:{line_number} declares a plugin before plugins:")
            current_plugin = {
                "id": _scalar_value(path, line_number, line, "  - id: "),
                "harnesses": {},
            }
            result["plugins"].append(current_plugin)
            current_harness = None
            harnesses_seen = False
        elif current_plugin is not None and line.startswith("    version: "):
            current_plugin["version"] = _scalar_value(
                path, line_number, line, "    version: "
            )
        elif current_plugin is not None and line.startswith("    description: "):
            current_plugin["description"] = _scalar_value(
                path, line_number, line, "    description: "
            )
        elif current_plugin is not None and line.startswith("    license: "):
            current_plugin["license"] = _scalar_value(
                path, line_number, line, "    license: "
            )
        elif current_plugin is not None and line.startswith("    category: "):
            current_plugin["category"] = _scalar_value(
                path, line_number, line, "    category: "
            )
        elif current_plugin is not None and line == "    harnesses:":
            harnesses_seen = True
            current_harness = None
        elif (
            current_plugin is not None
            and harnesses_seen
            and line.startswith("      ")
            and line.endswith(":")
        ):
            current_harness = line.strip().removesuffix(":")
            current_plugin["harnesses"][current_harness] = {}
        elif (
            current_plugin is not None
            and current_harness is not None
            and line.startswith("        name: ")
        ):
            current_plugin["harnesses"][current_harness]["name"] = _scalar_value(
                path, line_number, line, "        name: "
            )
        elif (
            current_plugin is not None
            and current_harness is not None
            and line.startswith("        skills: ")
        ):
            current_plugin["harnesses"][current_harness]["skills"] = _scalar_value(
                path, line_number, line, "        skills: "
            )
        elif (
            current_plugin is not None
            and current_harness is not None
            and line.startswith("        path: ")
        ):
            current_plugin["harnesses"][current_harness]["path"] = _scalar_value(
                path, line_number, line, "        path: "
            )
        else:
            raise ValueError(f"Unsupported line in {path}:{line_number}: {line}")

    if not plugins_seen:
        raise ValueError(f"{path} must contain a plugins: key")
    return _validate_marketplace_metadata(result, path)


def _scalar_value(path: Path, line_number: int, line: str, prefix: str) -> str:
    """Return a supported scalar value from the fallback YAML subset."""

    return line.removeprefix(prefix)


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
        _require_string_keys(plugin, plugin_context)

        extra_plugin = plugin.keys() - PLUGIN_ALLOWED_KEYS
        if extra_plugin:
            extra = ", ".join(sorted(extra_plugin))
            raise ValueError(f"{plugin_context} has unsupported keys: {extra}")

        missing_plugin = PLUGIN_REQUIRED_KEYS - plugin.keys()
        if missing_plugin:
            missing = ", ".join(sorted(missing_plugin))
            raise ValueError(f"{plugin_context} is missing keys: {missing}")

        for key in PLUGIN_SCALAR_KEYS:
            _require_string_scalar(
                plugin[key],
                f"{plugin_context}.{key}",
            )

        if plugin["id"] in plugin_ids:
            raise ValueError(f"{path} has duplicate plugin id: {plugin['id']}")
        plugin_ids.add(plugin["id"])

        harnesses = plugin["harnesses"]
        if not isinstance(harnesses, dict):
            raise ValueError(f"{path} plugin {plugin['id']} harnesses must be a mapping")

        for harness_name, harness in harnesses.items():
            if not isinstance(harness_name, str):
                raise ValueError(
                    f"{path} plugin {plugin['id']} harness key {harness_name} "
                    "must be a string"
                )
            if not isinstance(harness, dict):
                raise ValueError(
                    f"{path} plugin {plugin['id']} harness {harness_name} "
                    "must be a mapping"
                )
            _require_string_keys(
                harness, f"{path} plugin {plugin['id']} harness {harness_name}"
            )
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
            harness_public_name = (harness_name, harness["name"])
            if harness_public_name in harness_public_names:
                raise ValueError(
                    f"{path} has duplicate harness public name: {harness['name']}"
                )
            harness_public_names.add(harness_public_name)

    json.dumps(data)
    return data


def _require_string_scalar(value: Any, context: str) -> None:
    """Reject YAML scalar types that are not canonical string values."""

    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")


def _require_string_keys(mapping: dict[Any, Any], context: str) -> None:
    """Reject PyYAML mapping keys that are not canonical string keys."""

    for key in mapping:
        if not isinstance(key, str):
            raise ValueError(f"{context} key {key} must be a string")
