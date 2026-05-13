"""Expose a TOML parser for Python 3.9+ plugin runtimes."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _vendored_tomli_candidates() -> tuple[Path, ...]:
    package_file = Path(__file__).resolve()
    return (
        package_file.parent.parent / "tomli" / "__init__.py",
        package_file.parents[2] / "vendor" / "tomli" / "tomli" / "__init__.py",
    )


def _load_vendored_tomli() -> ModuleType:
    for vendor_init in _vendored_tomli_candidates():
        if not vendor_init.is_file():
            continue
        spec = importlib.util.spec_from_file_location("tomli", vendor_init)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules["tomli"] = module
        spec.loader.exec_module(module)
        return module
    candidates = ", ".join(str(path) for path in _vendored_tomli_candidates())
    raise ImportError(f"research-prompt could not load vendored tomli from: {candidates}")

try:
    tomllib = importlib.import_module("tomllib")
except ModuleNotFoundError as exc:
    if exc.name != "tomllib":
        raise
    try:
        tomllib = importlib.import_module("tomli")
    except ModuleNotFoundError as tomli_exc:
        if tomli_exc.name != "tomli":
            raise
        tomllib = _load_vendored_tomli()

__all__ = ["tomllib"]
