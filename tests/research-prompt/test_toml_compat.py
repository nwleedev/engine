from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "research-prompt"
    / "research_prompt"
    / "toml_compat.py"
)


def _load_source_toml_compat() -> ModuleType:
    spec = importlib.util.spec_from_file_location("source_toml_compat_under_test", SOURCE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tomllib_nested_module_not_found_is_re_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    def import_module(name: str) -> ModuleType:
        if name == "tomllib":
            raise ModuleNotFoundError("No module named 'nested_dependency'", name="nested_dependency")
        if name == "tomli":
            return ModuleType("tomli")
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", import_module)

    with pytest.raises(ModuleNotFoundError, match="nested_dependency") as exc_info:
        _load_source_toml_compat()

    assert exc_info.value.name == "nested_dependency"


def test_tomli_is_aliased_when_tomllib_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTOMLDecodeError(ValueError):
        pass

    fake_tomli = ModuleType("tomli")
    fake_tomli.loads = lambda source: {"source": source}
    fake_tomli.TOMLDecodeError = FakeTOMLDecodeError

    def import_module(name: str) -> ModuleType:
        if name == "tomllib":
            raise ModuleNotFoundError("No module named 'tomllib'", name="tomllib")
        if name == "tomli":
            return fake_tomli
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", import_module)

    module = _load_source_toml_compat()

    assert module.tomllib is fake_tomli
    assert module.tomllib.loads("value = 1\n") == {"source": "value = 1\n"}
    with pytest.raises(module.tomllib.TOMLDecodeError):
        raise module.tomllib.TOMLDecodeError("invalid toml")
