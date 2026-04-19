#!/usr/bin/env python3
"""
Plugin version bump script.

Usage:
  bump_version.py <plugin> <major|minor|patch|x.y.z>
  bump_version.py <plugin> --check
  bump_version.py --check-all
"""
import argparse
import json
import re
import sys
from pathlib import Path


def bump_semver(current: str, bump_type: str) -> str:
    """Calculate new version string. bump_type is major/minor/patch or explicit x.y.z."""
    if re.match(r'^\d+\.\d+\.\d+$', bump_type):
        return bump_type
    parts = current.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Invalid bump type '{bump_type}'. Use major, minor, patch, or x.y.z")


def read_json_field(file_path: Path, field: str) -> str:
    """Read a dotted field path from a JSON file. e.g. 'plugins.0.version'"""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    node = data
    for key in field.split('.'):
        node = node[int(key)] if key.isdigit() else node[key]
    return node


def write_json_field(file_path: Path, field: str, value: str) -> None:
    """Write a value at a dotted field path, preserving 2-space JSON formatting."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    keys = field.split('.')
    node = data
    for key in keys[:-1]:
        node = node[int(key)] if key.isdigit() else node[key]
    last = keys[-1]
    if last.isdigit():
        node[int(last)] = value
    else:
        node[last] = value
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_config(plugin_dir: Path) -> dict:
    """Load .version-bump.json from plugin directory."""
    config_path = plugin_dir / ".version-bump.json"
    if not config_path.exists():
        raise FileNotFoundError(f"No .version-bump.json in {plugin_dir}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_current_version(plugin_dir: Path, config: dict) -> str:
    """Read version from the first declared file in config."""
    first = config["files"][0]
    return read_json_field(plugin_dir / first["path"], first["field"])


def cmd_check(plugin_name: str, plugins_dir: Path) -> bool:
    """Print version info for a plugin. Returns True if all files are in sync."""
    plugin_dir = plugins_dir / plugin_name
    if not plugin_dir.is_dir():
        print(f"ERROR: Plugin directory not found: {plugin_dir}", file=sys.stderr)
        return False
    try:
        config = load_config(plugin_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False

    print(f"Version check: {plugin_name}")
    versions = []
    for entry in config["files"]:
        file_path = plugin_dir / entry["path"]
        if not file_path.exists():
            print(f"  MISSING: {entry['path']} ({entry['field']})")
            return False
        ver = read_json_field(file_path, entry["field"])
        print(f"  {entry['path']} ({entry['field']}): {ver}")
        versions.append(ver)

    unique = set(versions)
    if len(unique) > 1:
        print(f"\nDRIFT DETECTED — versions not in sync: {sorted(unique)}")
        return False
    print(f"\nIn sync at {versions[0]}")
    return True
