from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from collections.abc import Callable
from typing import Any

from tools.build.headers import GENERATED_NOTICE, markdown_header, python_header
from tools.build.source_files import source_file_exists


TRACEABLE_SUFFIXES = frozenset({".json", ".md", ".py", ".toml"})
GENERATED_REGISTRY_NAME = ".generated.json"
GENERATED_PLUGIN_ROOTS = (Path("plugins/codex"), Path("plugins/claude"))
VALID_SOURCE_ROOTS = frozenset({"plugin-sources", "packages"})


def registry_entry(target: str, source: str) -> dict[str, str]:
    """Return one generated tracing registry entry."""

    return {
        "target": target,
        "source": source,
        "notice": GENERATED_NOTICE,
    }


def registry_document(entries: list[dict[str, str]]) -> dict[str, Any]:
    """Return a generated tracing registry document sorted by target path."""

    return {"generated": sorted(entries, key=lambda entry: entry["target"])}


def validate_generated_tracing(root: Path) -> list[str]:
    """Validate generated plugin tracing headers and registry entries."""

    errors: list[str] = []
    for plugin_root in _iter_generated_plugin_roots(root):
        registry_targets = _load_registry_targets(root, plugin_root, errors)
        for generated_file in _iter_traceable_files(plugin_root):
            relative_path = generated_file.relative_to(root)
            target = generated_file.relative_to(plugin_root).as_posix()
            if target in registry_targets or _has_inline_tracing(root, generated_file):
                continue
            errors.append(f"missing generated tracing: {relative_path}")

    return errors


def _iter_generated_plugin_roots(root: Path) -> list[Path]:
    plugin_roots: list[Path] = []
    for generated_root in GENERATED_PLUGIN_ROOTS:
        harness_root = root / generated_root
        if not harness_root.is_dir():
            continue
        for path in sorted(harness_root.iterdir()):
            if path.is_dir():
                plugin_roots.append(path)
    return plugin_roots


def _iter_traceable_files(plugin_root: Path) -> list[Path]:
    return sorted(
        path
        for path in plugin_root.rglob("*")
        if path.is_file()
        and path.name != GENERATED_REGISTRY_NAME
        and path.suffix in TRACEABLE_SUFFIXES
    )


def _load_registry_targets(root: Path, plugin_root: Path, errors: list[str]) -> set[str]:
    registry_path = plugin_root / GENERATED_REGISTRY_NAME
    if not registry_path.exists():
        return set()

    relative_registry = registry_path.relative_to(root)
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid generated registry JSON in {relative_registry}: {exc.msg}")
        return set()

    if not isinstance(data, dict):
        errors.append(f"generated registry is not an object: {relative_registry}")
        return set()

    entries = data.get("generated")
    if not isinstance(entries, list):
        errors.append(f"{relative_registry} must have list generated")
        return set()

    targets: set[str] = set()
    for index, entry in enumerate(entries):
        target = _validate_registry_entry(
            root,
            plugin_root,
            relative_registry,
            index,
            entry,
            errors,
        )
        if target is not None:
            if target in targets:
                entry_path = f"{relative_registry} generated[{index}]"
                errors.append(f"duplicate generated registry target: {entry_path} {target}")
                continue
            targets.add(target)

    return targets


def _validate_registry_entry(
    root: Path,
    plugin_root: Path,
    relative_registry: Path,
    index: int,
    entry: Any,
    errors: list[str],
) -> str | None:
    entry_path = f"{relative_registry} generated[{index}]"
    if not isinstance(entry, dict):
        errors.append(f"malformed generated registry entry: {entry_path}")
        return None

    target = entry.get("target")
    source = entry.get("source")
    notice = entry.get("notice")
    if not all(isinstance(value, str) for value in (target, source, notice)):
        errors.append(f"malformed generated registry entry: {entry_path}")
        return None

    if notice == "":
        errors.append(f"malformed generated registry entry: {entry_path}")
        return None

    if notice != GENERATED_NOTICE:
        errors.append(f"malformed generated registry entry: {entry_path}")
        return None

    if not _is_safe_relative_target(target):
        errors.append(f"unsafe generated registry target: {entry_path} {target}")
        return None

    if not _is_safe_registry_source(source):
        errors.append(f"invalid generated registry source: {entry_path} {source}")
        return None

    if not _source_exists(root, source):
        errors.append(f"generated registry source is missing: {entry_path} {source}")
        return None

    target_path = plugin_root / target
    if not target_path.exists():
        errors.append(f"generated registry target is missing: {target_path.relative_to(root)}")
        return None

    return target


def _is_safe_relative_target(target: str) -> bool:
    target_path = PurePosixPath(target)
    return (
        not _has_unsafe_raw_segment(target)
        and "\\" not in target
        and target != GENERATED_REGISTRY_NAME
        and not target_path.is_absolute()
    )


def _is_safe_registry_source(source: str) -> bool:
    source_path = PurePosixPath(source)
    return (
        not _has_unsafe_raw_segment(source)
        and "\\" not in source
        and not source_path.is_absolute()
        and len(source_path.parts) > 1
        and source_path.parts[0] in VALID_SOURCE_ROOTS
    )


def _source_exists(root: Path, source: str) -> bool:
    return source_file_exists(root, root / source)


def _has_unsafe_raw_segment(path: str) -> bool:
    return any(segment in {"", ".", ".."} for segment in path.split("/"))


def _has_inline_tracing(root: Path, path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return _has_exact_markdown_header(root, text) or _has_exact_python_header(root, text)


def _has_exact_markdown_header(root: Path, text: str) -> bool:
    return _has_exact_header(
        root,
        text,
        notice_line=f"<!-- {GENERATED_NOTICE} -->",
        source_prefix="<!-- source: ",
        source_suffix=" -->",
        header_factory=markdown_header,
    )


def _has_exact_python_header(root: Path, text: str) -> bool:
    return _has_exact_header(
        root,
        text,
        notice_line=f"# {GENERATED_NOTICE}",
        source_prefix="# source: ",
        source_suffix="",
        header_factory=python_header,
    )


def _has_exact_header(
    root: Path,
    text: str,
    *,
    notice_line: str,
    source_prefix: str,
    source_suffix: str,
    header_factory: Callable[[str], str],
) -> bool:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0] != notice_line or lines[2] != "":
        return False

    source_line = lines[1]
    if not source_line.startswith(source_prefix):
        return False

    source = source_line.removeprefix(source_prefix)
    if source_suffix != "":
        if not source.endswith(source_suffix):
            return False
        source = source.removesuffix(source_suffix)

    return (
        _is_safe_registry_source(source)
        and _source_exists(root, source)
        and text.startswith(header_factory(source))
    )


__all__ = ["registry_document", "registry_entry", "validate_generated_tracing"]
