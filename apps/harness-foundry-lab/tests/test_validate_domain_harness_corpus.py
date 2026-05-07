import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path("apps/harness-foundry-lab")
FIXTURES = ROOT / "corpus" / "domain-harness" / "synthetic"
VALIDATOR = ROOT / "scripts" / "validate_domain_harness_corpus.py"
REPORTER = ROOT / "scripts" / "render_evaluation_report.py"
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
    return subprocess.run(
        ["python3", str(VALIDATOR), str(project_root), *extra_args],
        check=False,
        text=True,
        capture_output=True,
    )


def run_reporter(input_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(REPORTER), str(input_path)],
        check=False,
        text=True,
        capture_output=True,
    )


def read_fixture_contract(fixture_name: str) -> dict[str, object]:
    path = FIXTURES / fixture_name / "fixture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_valid_fixtures_pass(tmp_path):
    for fixture_name in VALID_FIXTURES:
        project_root = copy_fixture(tmp_path, fixture_name)

        result = run_validator(project_root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "domain harness validation passed" in result.stdout


def test_invalid_fixtures_fail_with_expected_rule_ids(tmp_path):
    for fixture_name in INVALID_FIXTURES:
        contract = read_fixture_contract(fixture_name)
        project_root = copy_fixture(tmp_path, fixture_name)

        result = run_validator(project_root, "--json")

        assert result.returncode == 1
        payload = json.loads(result.stdout)
        actual_rule_ids = {finding["rule_id"] for finding in payload["findings"]}
        assert set(contract["expected_rule_ids"]).issubset(actual_rule_ids)


def test_json_output_is_parseable_for_valid_fixture(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")

    result = run_validator(project_root, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["root"] == str(project_root.resolve())
    assert payload["findings"] == []


def test_missing_root_returns_usage_exit_code(tmp_path):
    missing_root = tmp_path / "missing"

    result = run_validator(missing_root)

    assert result.returncode == 2
    assert "unreadable project root" in result.stderr


def test_reporter_groups_validator_findings(tmp_path):
    project_root = copy_fixture(tmp_path, "invalid-missing-evals")
    validation_result = run_validator(project_root, "--json")
    input_path = tmp_path / "validation.json"
    input_path.write_text(validation_result.stdout, encoding="utf-8")

    result = run_reporter(input_path)

    assert result.returncode == 0
    assert "## Summary" in result.stdout
    assert "## Local fix candidates" in result.stdout
    assert "## Sanitized evaluation case candidates" in result.stdout
    assert "## Public-safety review" in result.stdout
    assert "public_safety_check" in result.stdout
    assert "missing-evals-file" in result.stdout


def test_report_without_public_safety_check_returns_warning(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")
    report_dir = project_root / "docs" / "domain-harness" / "evaluation-reports"
    report_dir.mkdir()
    report_path = report_dir / "2026-05-07-evaluation-report.md"
    report_path.write_text("# Report\n\nNo release review yet.\n", encoding="utf-8")

    result = run_validator(project_root, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    actual_rule_ids = {finding["rule_id"] for finding in payload["findings"]}
    assert "missing-public-safety-check" in actual_rule_ids


def test_warning_only_human_output_passes_with_warnings(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")
    report_dir = project_root / "docs" / "domain-harness" / "evaluation-reports"
    report_dir.mkdir()
    report_path = report_dir / "2026-05-07-evaluation-report.md"
    report_path.write_text("# Report\n\nNo release review yet.\n", encoding="utf-8")

    result = run_validator(project_root)

    assert result.returncode == 0
    assert "domain harness validation passed with warnings" in result.stdout
    assert "domain harness validation failed" not in result.stdout
    assert "missing-public-safety-check" in result.stdout


def test_sanitized_evaluation_case_without_public_safety_check_returns_warning(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")
    case_dir = project_root / "docs" / "domain-harness" / "sanitized-evaluation-cases"
    case_dir.mkdir()
    case_path = case_dir / "checkout-api-case.md"
    case_path.write_text("# Sanitized evaluation case\n\nNo release review yet.\n", encoding="utf-8")

    result = run_validator(project_root, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    findings = payload["findings"]
    assert any(
        finding["rule_id"] == "missing-public-safety-check"
        and finding["path"] == "docs/domain-harness/sanitized-evaluation-cases/checkout-api-case.md"
        for finding in findings
    )
