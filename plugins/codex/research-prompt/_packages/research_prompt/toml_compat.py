"""Expose a TOML parser for Python 3.9+ plugin runtimes."""

from __future__ import annotations

import importlib

try:
    tomllib = importlib.import_module("tomllib")
except ModuleNotFoundError as exc:
    if exc.name != "tomllib":
        raise
    tomllib = importlib.import_module("tomli")

__all__ = ["tomllib"]
