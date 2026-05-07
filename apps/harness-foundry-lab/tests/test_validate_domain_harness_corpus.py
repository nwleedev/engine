import json
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / "apps" / "harness-foundry-lab"
FIXTURES = ROOT / "corpus" / "domain-harness" / "synthetic"
VALIDATOR = ROOT / "scripts" / "validate_domain_harness_corpus.py"
BASE_VALIDATOR = (
    REPO_ROOT
    / "plugins"
    / "harness-foundry"
    / "skills"
    / "audit-domain-harness"
    / "scripts"
    / "validate_domain_harness.py"
)
REPORTER = ROOT / "scripts" / "render_evaluation_report.py"


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


def run_base_validator(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(BASE_VALIDATOR), str(project_root), *extra_args],
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


def write_minimal_domain_harness(project_root: Path, *, status: str = "active") -> None:
    harness_root = project_root / "docs" / "domain-harness"
    domain_root = harness_root / "checkout-api"
    domain_root.mkdir(parents=True)
    (domain_root / "spec.md").write_text(
        "\n".join(
            [
                "# Checkout API Harness",
                "Implementation scope",
                "Test strategy",
                "Security review",
                "Dependency policy",
            ]
        ),
        encoding="utf-8",
    )
    (domain_root / "evals.md").write_text("# Evals\n", encoding="utf-8")
    (domain_root / "scaffold.md").write_text("# Scaffold\n", encoding="utf-8")
    (harness_root / "index.md").write_text(
        "\n".join(
            [
                "# Domain Harness Registry",
                "",
                "| domain | work_type | status | owner | spec | evals | scaffold | last_reviewed |",
                "|---|---|---|---|---|---|---|---|",
                f"| checkout-api | development | {status} | platform-team | `checkout-api/spec.md` | `checkout-api/evals.md` | `checkout-api/scaffold.md` | 2026-05-06 |",
            ]
        ),
        encoding="utf-8",
    )


def test_wrapper_forwards_base_validator_finding(tmp_path):
    project_root = tmp_path / "invalid-status"
    write_minimal_domain_harness(project_root, status="paused")

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "invalid-status",
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Invalid status for domain checkout-api: paused.",
        "domain": "checkout-api",
    } in payload["findings"]


def test_wrapper_json_matches_base_validator_without_lab_specific_artifacts(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")

    wrapper_result = run_validator(project_root, "--json")
    base_result = run_base_validator(project_root, "--json")

    assert wrapper_result.returncode == base_result.returncode
    assert json.loads(wrapper_result.stdout) == json.loads(base_result.stdout)


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


def test_unreadable_public_safety_candidates_return_warning_findings(tmp_path):
    project_root = copy_fixture(tmp_path, "valid-dev")
    report_dir = project_root / "docs" / "domain-harness" / "evaluation-reports"
    report_dir.mkdir()
    directory_candidate = report_dir / "nested.md"
    directory_candidate.mkdir()
    binary_candidate = report_dir / "legacy.md"
    binary_candidate.write_bytes(b"\xff\xfe\x00")

    result = run_validator(project_root, "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    unreadable_findings = sorted(
        [
            finding
            for finding in payload["findings"]
            if finding["rule_id"] == "unreadable-public-safety-artifact"
        ],
        key=lambda finding: finding["path"],
    )
    assert unreadable_findings == [
        {
            "rule_id": "unreadable-public-safety-artifact",
            "severity": "warning",
            "path": "docs/domain-harness/evaluation-reports/legacy.md",
            "message": "Public-safety artifact candidate is not a readable UTF-8 file.",
            "domain": "",
        },
        {
            "rule_id": "unreadable-public-safety-artifact",
            "severity": "warning",
            "path": "docs/domain-harness/evaluation-reports/nested.md",
            "message": "Public-safety artifact candidate is not a readable UTF-8 file.",
            "domain": "",
        },
    ]
