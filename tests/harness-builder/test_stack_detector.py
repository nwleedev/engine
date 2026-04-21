import importlib.util
import json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-builder/scripts"

_spec = importlib.util.spec_from_file_location(
    "harness_builder.stack_detector", SCRIPTS_DIR / "stack_detector.py"
)
assert _spec is not None and _spec.loader is not None
sd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sd)


def test_detects_typescript_from_two_files(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert "TypeScript" in result["languages"]
    assert result["confidence"] == "high"


def test_detects_nextjs_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "^14.0.0"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert "Next.js" in result["frameworks"]


def test_detects_react_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert "React" in result["frameworks"]


def test_detects_python_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'myapp'")
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    result = sd.detect_stack(str(tmp_path))
    assert "Python" in result["languages"]
    assert result["confidence"] == "high"


def test_detects_go_from_go_mod(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com\n\ngo 1.21")
    result = sd.detect_stack(str(tmp_path))
    assert "Go" in result["languages"]


def test_detects_rust_from_cargo(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'myapp'\nversion = '0.1.0'")
    result = sd.detect_stack(str(tmp_path))
    assert "Rust" in result["languages"]


def test_confidence_low_when_one_file(tmp_path):
    (tmp_path / "package.json").write_text('{}')
    result = sd.detect_stack(str(tmp_path))
    assert result["confidence"] == "low"


def test_confidence_low_when_no_files(tmp_path):
    result = sd.detect_stack(str(tmp_path))
    assert result["confidence"] == "low"


def test_confidence_high_with_two_root_files(tmp_path):
    (tmp_path / "package.json").write_text('{}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert result["confidence"] == "high"


def test_detects_eslint_v9_version(tmp_path):
    (tmp_path / "package.json").write_text('{"devDependencies": {"eslint": "^9.2.0"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert result.get("eslint_version") == "9.2.0"


def test_detects_eslint_v8_version(tmp_path):
    (tmp_path / "package.json").write_text('{"devDependencies": {"eslint": "^8.57.0"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert result.get("eslint_version") == "8.57.0"


def test_no_eslint_version_when_not_present(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert "eslint_version" not in result


def test_detects_existing_eslint_flat_config(tmp_path):
    (tmp_path / "eslint.config.js").write_text("export default []")
    (tmp_path / "package.json").write_text('{}')
    result = sd.detect_stack(str(tmp_path))
    assert "eslint" in result["linters_existing"]


def test_detects_existing_eslint_legacy(tmp_path):
    (tmp_path / ".eslintrc.json").write_text("{}")
    (tmp_path / "package.json").write_text('{}')
    result = sd.detect_stack(str(tmp_path))
    assert "eslint" in result["linters_existing"]


def test_detects_existing_ruff_via_section(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 88\n")
    (tmp_path / "requirements.txt").write_text("ruff\n")
    result = sd.detect_stack(str(tmp_path))
    assert "ruff" in result["linters_existing"]


def test_ruff_not_detected_without_section(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    result = sd.detect_stack(str(tmp_path))
    assert "ruff" not in result["linters_existing"]


def test_monorepo_detection(tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "go.mod").write_text("module api\n\ngo 1.21")
    result = sd.detect_stack(str(tmp_path))
    assert result["monorepo"] is True


def test_not_monorepo_when_files_at_root(tmp_path):
    (tmp_path / "package.json").write_text('{}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert result["monorepo"] is False


def test_npm_package_manager_detected(tmp_path):
    (tmp_path / "package.json").write_text('{}')
    (tmp_path / "package-lock.json").write_text('{}')
    (tmp_path / "tsconfig.json").write_text("{}")
    result = sd.detect_stack(str(tmp_path))
    assert "npm" in result["package_managers"]


def test_go_package_manager_detected(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com\n\ngo 1.21")
    result = sd.detect_stack(str(tmp_path))
    assert "go" in result["package_managers"]


def test_result_has_required_keys(tmp_path):
    result = sd.detect_stack(str(tmp_path))
    for key in ("languages", "frameworks", "linters_existing", "linters_missing",
                "monorepo", "package_managers", "confidence"):
        assert key in result
