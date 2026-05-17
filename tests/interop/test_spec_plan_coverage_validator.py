from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "plugin-sources"
    / "shared-skills"
    / "skills"
    / "spec-plan-coverage"
    / "validate_spec_plan_coverage.py"
)
FIXTURES = ROOT / "tests" / "fixtures" / "shared-workflow" / "spec-plan-coverage"


def load_validator():
    """Load the source validator so tests exercise the plugin script directly."""

    spec = importlib.util.spec_from_file_location("validate_spec_plan_coverage", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def test_validator_script_is_bundled_for_codex_and_claude() -> None:
    assert VALIDATOR.exists()
    assert (
        ROOT
        / "plugins"
        / "codex"
        / "shared-skills"
        / "skills"
        / "spec-plan-coverage"
        / "validate_spec_plan_coverage.py"
    ).exists()
    assert (
        ROOT
        / "plugins"
        / "claude"
        / "shared-skills"
        / "skills"
        / "spec-plan-coverage"
        / "validate_spec_plan_coverage.py"
    ).exists()


def test_complete_fixture_is_done_candidate() -> None:
    validator = load_validator()

    report = validator.validate_document(read_fixture("complete"))

    assert report["final_status"] == "done_candidate"
    assert report["blocking_codes"] == []
    assert report["coverage_matrix"][0]["coverage_status"] == "covered"


def test_negative_fixtures_emit_expected_failure_codes() -> None:
    validator = load_validator()
    expected_codes = json.loads(
        (FIXTURES / "expected-failure-codes.json").read_text(encoding="utf-8")
    )

    for fixture_name, failure_codes in sorted(expected_codes.items()):
        report = validator.validate_document(read_fixture(fixture_name))
        assert report["final_status"] == "blocked"
        assert set(failure_codes) <= set(report["blocking_codes"])


def test_cli_writes_machine_json_and_redacted_markdown(tmp_path: Path) -> None:
    json_report = tmp_path / "coverage-report.json"
    markdown_report = tmp_path / "coverage-report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(FIXTURES / "missing-validation.json"),
            "--json-output",
            str(json_report),
            "--markdown-output",
            str(markdown_report),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    report = json.loads(json_report.read_text(encoding="utf-8"))
    redacted = markdown_report.read_text(encoding="utf-8")
    assert "missing_validation" in report["blocking_codes"]
    assert "missing_validation" in redacted
    assert "confidential source text" not in redacted
    assert "source_location" in redacted
