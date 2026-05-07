import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / "apps" / "harness-foundry-lab"
FIXTURES = ROOT / "corpus" / "domain-harness" / "synthetic"
VALIDATOR = (
    REPO_ROOT
    / "plugins"
    / "harness-foundry"
    / "skills"
    / "audit-domain-harness"
    / "scripts"
    / "validate_domain_harness.py"
)
VALID_FIXTURES = ("valid-dev", "valid-nondev", "valid-mixed")
INVALID_FIXTURES = (
    "invalid-missing-registry",
    "invalid-missing-spec",
    "invalid-missing-evals",
    "invalid-index-json-source",
    "invalid-auto-hooks",
    "invalid-auto-mcp",
    "invalid-nondev-no-source-policy",
    "invalid-mixed-no-split-guardrails",
)


def copy_fixture(tmp_path: Path, fixture_name: str) -> Path:
    source = FIXTURES / fixture_name
    target = tmp_path / fixture_name
    shutil.copytree(source, target)
    return target


def run_validator(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    if not VALIDATOR.exists():
        pytest.fail(f"validator prerequisite missing: {VALIDATOR}")

    return subprocess.run(
        ["python3", str(VALIDATOR), str(project_root), *extra_args],
        check=False,
        text=True,
        capture_output=True,
    )


def read_fixture_contract(fixture_name: str) -> dict[str, object]:
    path = FIXTURES / fixture_name / "fixture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_valid_domain_harness_fixtures_pass(tmp_path):
    for fixture_name in VALID_FIXTURES:
        project_root = copy_fixture(tmp_path, fixture_name)

        result = run_validator(project_root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "domain harness validation passed" in result.stdout


def test_invalid_domain_harness_fixtures_fail_with_expected_rule_ids(tmp_path):
    for fixture_name in INVALID_FIXTURES:
        contract = read_fixture_contract(fixture_name)
        project_root = copy_fixture(tmp_path, fixture_name)

        result = run_validator(project_root, "--json")

        assert result.returncode == 1
        payload = json.loads(result.stdout)
        actual_rule_ids = {finding["rule_id"] for finding in payload["findings"]}
        assert set(contract["expected_rule_ids"]).issubset(actual_rule_ids)


def test_domain_harness_json_output_is_parseable_for_valid_fixture(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")

    result = run_validator(project_root, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["root"] == str(project_root.resolve())
    assert payload["findings"] == []


def test_domain_harness_missing_root_returns_usage_exit_code(tmp_path):
    missing_root = tmp_path / "missing"

    result = run_validator(missing_root)

    assert result.returncode == 2
    assert "unreadable project root" in result.stderr
