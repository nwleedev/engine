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
