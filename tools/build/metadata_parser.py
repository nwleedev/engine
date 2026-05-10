from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.build.metadata_validator import _validate_marketplace_metadata


SUPPORTED_INDENT_LEVELS = {0, 2, 4, 6, 8}
BLOCK_SCALAR_VALUES = {"|", ">", "|-", ">-", "|+", ">+"}


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
            _preflight_scalar_value(path, line_number, line.split(": ", 1)[1])


def _preflight_scalar_value(path: Path, line_number: int, raw_value: str) -> None:
    """Reject scalar spellings unsupported by the fallback parser."""

    if raw_value.startswith(" "):
        raise ValueError(
            "extra spaces after mapping separator are not supported in "
            f"{path}:{line_number}"
        )
    value = raw_value.strip()
    if value in BLOCK_SCALAR_VALUES:
        raise ValueError(f"block scalar values are not supported in {path}:{line_number}")
    if value.startswith(("&", "*", "<<")):
        raise ValueError(
            "YAML anchors, aliases, and merge keys are not supported in "
            f"{path}:{line_number}"
        )
    if value.startswith("!"):
        raise ValueError(f"YAML tags are not supported in {path}:{line_number}")
    if value.startswith(("'", '"')):
        raise ValueError(f"quoted scalar values are not supported in {path}:{line_number}")
    if value.startswith(("[", "{")):
        raise ValueError(
            f"inline collection values are not supported in {path}:{line_number}"
        )


def _parse_marketplace_without_yaml(path: Path, text: str) -> dict[str, Any]:
    """Parse the current marketplace YAML subset without external packages."""

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
            result["name"] = _scalar_value(line, "name: ")
        elif line.startswith("display_name: "):
            result["display_name"] = _scalar_value(line, "display_name: ")
        elif line.startswith("description: "):
            result["description"] = _scalar_value(line, "description: ")
        elif line == "owner:":
            result["owner"] = {}
        elif line.startswith("  name: ") and isinstance(result.get("owner"), dict):
            result["owner"]["name"] = _scalar_value(line, "  name: ")
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
                "id": _scalar_value(line, "  - id: "),
                "harnesses": {},
            }
            result["plugins"].append(current_plugin)
            current_harness = None
            harnesses_seen = False
        elif current_plugin is not None and line.startswith("    version: "):
            current_plugin["version"] = _scalar_value(line, "    version: ")
        elif current_plugin is not None and line.startswith("    description: "):
            current_plugin["description"] = _scalar_value(line, "    description: ")
        elif current_plugin is not None and line.startswith("    license: "):
            current_plugin["license"] = _scalar_value(line, "    license: ")
        elif current_plugin is not None and line.startswith("    category: "):
            current_plugin["category"] = _scalar_value(line, "    category: ")
        elif current_plugin is not None and line == "    harnesses:":
            harnesses_seen = True
            current_harness = None
        elif _is_harness_header(current_plugin, harnesses_seen, line):
            current_harness = line.strip().removesuffix(":")
            current_plugin["harnesses"][current_harness] = {}
        elif _is_harness_field(current_plugin, current_harness, line, "name"):
            current_plugin["harnesses"][current_harness]["name"] = _scalar_value(
                line, "        name: "
            )
        elif _is_harness_field(current_plugin, current_harness, line, "skills"):
            current_plugin["harnesses"][current_harness]["skills"] = _scalar_value(
                line, "        skills: "
            )
        elif _is_harness_field(current_plugin, current_harness, line, "path"):
            current_plugin["harnesses"][current_harness]["path"] = _scalar_value(
                line, "        path: "
            )
        else:
            raise ValueError(f"Unsupported line in {path}:{line_number}: {line}")

    if not plugins_seen:
        raise ValueError(f"{path} must contain a plugins: key")
    return _validate_marketplace_metadata(result, path)


def _is_harness_header(
    current_plugin: dict[str, Any] | None,
    harnesses_seen: bool,
    line: str,
) -> bool:
    """Return whether a line opens a harness mapping."""

    return (
        current_plugin is not None
        and harnesses_seen
        and line.startswith("      ")
        and line.endswith(":")
    )


def _is_harness_field(
    current_plugin: dict[str, Any] | None,
    current_harness: str | None,
    line: str,
    field: str,
) -> bool:
    """Return whether a line assigns a field under the current harness."""

    return (
        current_plugin is not None
        and current_harness is not None
        and line.startswith(f"        {field}: ")
    )


def _scalar_value(line: str, prefix: str) -> str:
    """Return a supported scalar value from the fallback YAML subset."""

    return line.removeprefix(prefix)
