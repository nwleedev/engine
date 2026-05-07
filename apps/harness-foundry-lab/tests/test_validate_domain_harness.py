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


def write_minimal_domain_harness(
    project_root: Path,
    *,
    work_type: str = "development",
    status: str = "active",
    spec_path: str = "checkout-api/spec.md",
    evals_path: str = "checkout-api/evals.md",
    scaffold_path: str = "checkout-api/scaffold.md",
    extra_index_content: str = "",
) -> None:
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
    if scaffold_path == "checkout-api/scaffold.md":
        (domain_root / "scaffold.md").write_text("# Scaffold\n", encoding="utf-8")
    (harness_root / "index.md").write_text(
        "\n".join(
            [
                "# Domain Harness Registry",
                "",
                "| domain | work_type | status | owner | spec | evals | scaffold | last_reviewed |",
                "|---|---|---|---|---|---|---|---|",
                f"| checkout-api | {work_type} | {status} | platform-team | `{spec_path}` | `{evals_path}` | `{scaffold_path}` | 2026-05-06 |",
                extra_index_content,
            ]
        ),
        encoding="utf-8",
    )


def test_valid_domain_harness_fixtures_pass(tmp_path):
    for fixture_name in VALID_FIXTURES:
        project_root = copy_fixture(tmp_path, fixture_name)

        result = run_validator(project_root, "--json")

        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert payload["findings"] == []


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


def test_invalid_work_type_returns_domain_finding(tmp_path):
    project_root = tmp_path / "invalid-work-type"
    write_minimal_domain_harness(project_root, work_type="operations")

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "invalid-work-type",
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Invalid work_type for domain checkout-api: operations.",
        "domain": "checkout-api",
    } in payload["findings"]


def test_missing_scaffold_file_returns_domain_finding(tmp_path):
    project_root = tmp_path / "missing-scaffold"
    write_minimal_domain_harness(project_root, scaffold_path="checkout-api/missing-scaffold.md")

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "missing-scaffold-file",
        "severity": "error",
        "path": "docs/domain-harness/checkout-api/missing-scaffold.md",
        "message": "Active registry row for checkout-api points to a missing file.",
        "domain": "checkout-api",
    } in payload["findings"]


@pytest.mark.parametrize(
    ("path_overrides", "expected_rule_id"),
    [
        ({"spec_path": ""}, "missing-spec-file"),
        ({"evals_path": ""}, "missing-evals-file"),
        ({"scaffold_path": ""}, "missing-scaffold-file"),
    ],
)
def test_empty_registry_artifact_reference_returns_domain_finding(
    tmp_path, path_overrides, expected_rule_id
):
    project_root = tmp_path / f"empty-{expected_rule_id}"
    write_minimal_domain_harness(project_root, **path_overrides)

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": expected_rule_id,
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Active registry row for checkout-api has an empty registry value.",
        "domain": "checkout-api",
    } in payload["findings"]


def test_invalid_status_returns_domain_finding_at_registry_path(tmp_path):
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


def test_registry_parser_ignores_unrelated_later_pipe_table(tmp_path):
    project_root = tmp_path / "later-table"
    write_minimal_domain_harness(
        project_root,
        extra_index_content="\n".join(
            [
                "",
                "## Notes",
                "",
                "| item | value |",
                "|---|---|",
                "| unrelated | ignored |",
            ]
        ),
    )

    result = run_validator(project_root, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["findings"] == []


def test_registry_parser_does_not_fallback_to_later_registry_shaped_table(tmp_path):
    project_root = tmp_path / "malformed-first-table"
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
                "| domain | work_type | status |",
                "|---|---|---|",
                "| checkout-api | development | active |",
                "",
                "## Example",
                "",
                "| domain | work_type | status | owner | spec | evals | scaffold | last_reviewed |",
                "|---|---|---|---|---|---|---|---|",
                "| checkout-api | development | active | platform-team | `checkout-api/spec.md` | `checkout-api/evals.md` | `checkout-api/scaffold.md` | 2026-05-06 |",
            ]
        ),
        encoding="utf-8",
    )

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "registry-parse-error",
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Registry table missing columns: owner, spec, evals, scaffold, last_reviewed.",
        "domain": "",
    } in payload["findings"]


def test_registry_path_directory_returns_structured_missing_registry_finding(tmp_path):
    project_root = tmp_path / "directory-registry"
    index_path = project_root / "docs" / "domain-harness" / "index.md"
    index_path.mkdir(parents=True)

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "missing-registry",
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Missing docs/domain-harness/index.md registry.",
        "domain": "",
    } in payload["findings"]


def test_unreadable_registry_returns_structured_finding(tmp_path):
    project_root = tmp_path / "unreadable-registry"
    harness_root = project_root / "docs" / "domain-harness"
    harness_root.mkdir(parents=True)
    (harness_root / "index.md").write_bytes(b"\xff\xfe\x00")

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert {
        "rule_id": "unreadable-registry",
        "severity": "error",
        "path": "docs/domain-harness/index.md",
        "message": "Registry file must be a readable UTF-8 Markdown file.",
        "domain": "",
    } in payload["findings"]


@pytest.mark.parametrize(
    ("artifact_path", "expected_path"),
    [
        ("checkout-api/spec.md", "docs/domain-harness/checkout-api/spec.md"),
        ("checkout-api/evals.md", "docs/domain-harness/checkout-api/evals.md"),
        ("checkout-api/scaffold.md", "docs/domain-harness/checkout-api/scaffold.md"),
    ],
)
def test_unreadable_harness_artifact_returns_structured_finding(
    tmp_path, artifact_path, expected_path
):
    project_root = tmp_path / "unreadable-artifact"
    write_minimal_domain_harness(project_root)
    (project_root / "docs" / "domain-harness" / artifact_path).write_bytes(b"\xff\xfe\x00")

    result = run_validator(project_root, "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    matching_findings = [
        finding
        for finding in payload["findings"]
        if finding["rule_id"] == "unreadable-harness-artifact"
        and finding["path"] == expected_path
    ]
    assert matching_findings == [
        {
            "rule_id": "unreadable-harness-artifact",
            "severity": "error",
            "path": expected_path,
            "message": "Harness artifact must be a readable UTF-8 Markdown file.",
            "domain": "checkout-api",
        }
    ]
