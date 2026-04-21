import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-builder/scripts"

_spec = importlib.util.spec_from_file_location(
    "harness_builder.linter_config", SCRIPTS_DIR / "linter_config.py"
)
assert _spec is not None and _spec.loader is not None
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)


def test_eslint_v9_uses_flat_config(tmp_path):
    path, fmt = lc.get_linter_config_path("eslint", "9.2.0", str(tmp_path))
    assert Path(path).name == "eslint.config.js"
    assert fmt == "flat"


def test_eslint_v8_uses_legacy_config(tmp_path):
    path, fmt = lc.get_linter_config_path("eslint", "8.57.0", str(tmp_path))
    assert Path(path).name == ".eslintrc.json"
    assert fmt == "legacy"


def test_eslint_none_version_defaults_to_flat(tmp_path):
    path, fmt = lc.get_linter_config_path("eslint", None, str(tmp_path))
    assert Path(path).name == "eslint.config.js"
    assert fmt == "flat"


def test_eslint_exact_v9_boundary(tmp_path):
    path, fmt = lc.get_linter_config_path("eslint", "9.0.0", str(tmp_path))
    assert fmt == "flat"


def test_eslint_v8_boundary(tmp_path):
    path, fmt = lc.get_linter_config_path("eslint", "8.0.0", str(tmp_path))
    assert fmt == "legacy"


def test_prettier_config_path(tmp_path):
    path, fmt = lc.get_linter_config_path("prettier", None, str(tmp_path))
    assert Path(path).name == ".prettierrc.json"
    assert fmt == "json"


def test_ruff_config_path_and_format(tmp_path):
    path, fmt = lc.get_linter_config_path("ruff", None, str(tmp_path))
    assert Path(path).name == "pyproject.toml"
    assert fmt == "toml-section"


def test_golangci_config_path(tmp_path):
    path, fmt = lc.get_linter_config_path("golangci-lint", None, str(tmp_path))
    assert Path(path).name == ".golangci.yml"
    assert fmt == "yaml"


def test_stylelint_config_path(tmp_path):
    path, fmt = lc.get_linter_config_path("stylelint", None, str(tmp_path))
    assert Path(path).name == ".stylelintrc.json"
    assert fmt == "json"


def test_clippy_config_path(tmp_path):
    path, fmt = lc.get_linter_config_path("clippy", None, str(tmp_path))
    assert Path(path).name == "Cargo.toml"
    assert fmt == "toml-section"


def test_skip_existing_eslint_flat(tmp_path):
    (tmp_path / "eslint.config.js").write_text("export default []")
    assert lc.should_skip_existing("eslint", str(tmp_path)) is True


def test_skip_existing_eslint_legacy(tmp_path):
    (tmp_path / ".eslintrc.json").write_text("{}")
    assert lc.should_skip_existing("eslint", str(tmp_path)) is True


def test_skip_existing_prettier(tmp_path):
    (tmp_path / ".prettierrc.json").write_text("{}")
    assert lc.should_skip_existing("prettier", str(tmp_path)) is True


def test_skip_existing_ruff_with_section(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 88\n")
    assert lc.should_skip_existing("ruff", str(tmp_path)) is True


def test_no_skip_ruff_without_section(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    assert lc.should_skip_existing("ruff", str(tmp_path)) is False


def test_no_skip_when_absent(tmp_path):
    assert lc.should_skip_existing("eslint", str(tmp_path)) is False


def test_unknown_linter_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError, match="Unknown linter"):
        lc.get_linter_config_path("nonexistent-linter", None, str(tmp_path))
