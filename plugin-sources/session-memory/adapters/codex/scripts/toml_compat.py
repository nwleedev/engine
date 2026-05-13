"""Load a TOML parser for standalone Codex scripts."""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_toml_module() -> ModuleType:
    try:
        return importlib.import_module("tomllib")
    except ModuleNotFoundError as exc:
        if exc.name != "tomllib":
            raise

    try:
        return importlib.import_module("tomli")
    except ModuleNotFoundError as exc:
        if exc.name != "tomli":
            raise

    return _load_vendored_tomli()


def _load_vendored_tomli() -> ModuleType:
    checked_paths = _vendored_tomli_paths()
    vendored_init = next((path for path in checked_paths if path.is_file()), None)
    if vendored_init is None:
        checked = ", ".join(str(path) for path in checked_paths)
        raise ImportError(f"vendored tomli not found; checked: {checked}")

    module_name = "_session_memory_vendored_tomli"
    spec = importlib.util.spec_from_file_location(
        module_name,
        vendored_init,
        submodule_search_locations=[str(vendored_init.parent)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"vendored tomli cannot be loaded from {vendored_init}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise ImportError(f"vendored tomli cannot be loaded from {vendored_init}") from exc
    return module


def _vendored_tomli_paths() -> list[Path]:
    script_path = Path(__file__).resolve()
    return [
        script_path.parent.parent / "_packages" / "tomli" / "__init__.py",
        *_repo_vendor_tomli_paths(script_path),
    ]


def _repo_vendor_tomli_paths(script_path: Path) -> list[Path]:
    vendor_parts = ("packages", "vendor", "tomli", "tomli", "__init__.py")
    return [parent.joinpath(*vendor_parts) for parent in script_path.parents]
