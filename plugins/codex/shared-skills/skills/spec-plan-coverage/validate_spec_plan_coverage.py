# GENERATED FILE - DO NOT EDIT
# source: plugin-sources/shared-skills/skills/spec-plan-coverage/validate_spec_plan_coverage.py

#!/usr/bin/env python3
"""Validate spec-to-plan coverage from a redacted JSON workflow artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BLOCKING_ORDER = (
    "missing_source",
    "missing_acceptance_link",
    "multi_claim_clause",
    "orphan_task",
    "needs_spec_mapping",
    "missing_plan",
    "missing_validation",
    "missing_fallback",
    "missing_evidence",
    "stale_evidence",
    "unresolved_risk",
    "not_run_hidden",
    "missing_coverage_report",
    "unjustified_fixture",
    "fixture_overgrowth",
    "unapproved_mock",
    "missing_real_boundary_check",
    "test_only_behavior",
)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _ids(rows: list[dict[str, Any]], key: str) -> set[str]:
    return {
        item
        for row in rows
        for item in _as_list(row.get(key))
        if isinstance(item, str) and item
    }


def _add_code(codes: list[str], code: str) -> None:
    if code not in codes:
        codes.append(code)


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    """Return a machine-readable Coverage Report for a workflow JSON document."""

    spec_ledger = _as_list(document.get("spec_ledger"))
    plan_contract = _as_list(document.get("plan_contract"))
    test_plan = _as_list(document.get("test_plan_contract"))
    evidence = _as_list(document.get("implementation_evidence"))
    fixtures = _as_list(document.get("fixture_governance"))
    verification_gate = document.get("verification_gate") or {}
    fixture_budget = document.get("fixture_budget") or {}
    blocking_codes: list[str] = []
    coverage_matrix: list[dict[str, Any]] = []

    planned_clause_ids = _ids(plan_contract, "linked_spec_clause_ids")
    tested_clause_ids = _ids(test_plan, "linked_spec_clause_ids")
    evidenced_clause_ids = _ids(evidence, "linked_spec_clause_ids")
    stale_clause_ids = {
        item
        for row in evidence
        if row.get("fresh") is False or row.get("result") == "stale"
        for item in _as_list(row.get("linked_spec_clause_ids"))
        if isinstance(item, str) and item
    }

    for task in plan_contract:
        if not _as_list(task.get("linked_requirement_ids")):
            _add_code(blocking_codes, "orphan_task")
        if not _as_list(task.get("linked_spec_clause_ids")):
            _add_code(blocking_codes, "needs_spec_mapping")
        if not task.get("fallback"):
            _add_code(blocking_codes, "missing_fallback")

    for clause in spec_ledger:
        clause_id = str(clause.get("spec_clause_id") or "")
        clause_codes: list[str] = []
        if not clause.get("source_location"):
            clause_codes.append("missing_source")
        if not _as_list(clause.get("linked_requirement_ids")):
            clause_codes.append("missing_acceptance_link")
        if int(clause.get("claim_count") or len(_as_list(clause.get("claims"))) or 1) > 1:
            clause_codes.append("multi_claim_clause")
        if clause.get("status") in {"unresolved", "open_risk"}:
            clause_codes.append("unresolved_risk")
        if clause_id and clause_id not in planned_clause_ids:
            clause_codes.append("missing_plan")

        linked_tasks = [
            task
            for task in plan_contract
            if clause_id in _as_list(task.get("linked_spec_clause_ids"))
        ]
        if linked_tasks and not any(task.get("validation_method") for task in linked_tasks):
            clause_codes.append("missing_validation")
        if clause_id and clause_id not in evidenced_clause_ids:
            clause_codes.append("missing_evidence")
        if clause_id in stale_clause_ids:
            clause_codes.append("stale_evidence")

        coverage_status = "covered" if not clause_codes else clause_codes[0]
        for code in clause_codes:
            _add_code(blocking_codes, code)
        coverage_matrix.append(
            {
                "spec_clause_id": clause_id,
                "source_location": clause.get("source_location", ""),
                "plan_task_ids": [
                    str(task.get("task_id"))
                    for task in linked_tasks
                    if task.get("task_id")
                ],
                "test_or_check_ids": [
                    str(test.get("test_or_check_id"))
                    for test in test_plan
                    if clause_id in _as_list(test.get("linked_spec_clause_ids"))
                    and test.get("test_or_check_id")
                ],
                "evidence_ids": [
                    str(item.get("evidence_id"))
                    for item in evidence
                    if clause_id in _as_list(item.get("linked_spec_clause_ids"))
                    and item.get("evidence_id")
                ],
                "coverage_status": coverage_status,
            }
        )

    if verification_gate.get("requires_coverage_report") and not _as_list(
        verification_gate.get("coverage_report_ids")
    ):
        _add_code(blocking_codes, "missing_coverage_report")
    if verification_gate.get("not_run_items_hidden") or (
        _as_list(verification_gate.get("not_run_items"))
        and not _as_list(verification_gate.get("disclosed_not_run_items"))
    ):
        _add_code(blocking_codes, "not_run_hidden")

    fixture_ids = {
        item
        for test in test_plan
        for item in _as_list(test.get("fixture_governance_ids"))
        if isinstance(item, str) and item
    }
    governed_fixture_ids = {
        str(fixture.get("fixture_id"))
        for fixture in fixtures
        if fixture.get("fixture_id")
    }
    if fixture_ids - governed_fixture_ids:
        _add_code(blocking_codes, "unjustified_fixture")

    for fixture in fixtures:
        required = (
            "fixture_id",
            "linked_scenario_ids",
            "linked_spec_clause_ids",
            "justification",
            "owner",
            "drift_check",
            "expiry_or_update_trigger",
        )
        if any(not fixture.get(field) for field in required):
            _add_code(blocking_codes, "unjustified_fixture")
        if fixture.get("real_boundary_preferred") is False and not fixture.get(
            "high_fidelity_boundary"
        ):
            _add_code(blocking_codes, "missing_real_boundary_check")

    new_fixture_count = int(fixture_budget.get("new_fixture_count") or 0)
    new_mock_count = int(fixture_budget.get("new_mock_count") or 0)
    approved_count = int(fixture_budget.get("approved_new_fixture_count") or 0)
    approved_mock_count = int(fixture_budget.get("approved_new_mock_count") or 0)
    if new_fixture_count + new_mock_count > approved_count:
        _add_code(blocking_codes, "fixture_overgrowth")
    if new_mock_count > approved_mock_count:
        _add_code(blocking_codes, "unapproved_mock")
    if fixture_budget.get("test_only_behavior"):
        _add_code(blocking_codes, "test_only_behavior")
    if fixtures and not any(test.get("boundary_evidence") for test in test_plan):
        _add_code(blocking_codes, "missing_real_boundary_check")

    ordered_codes = [code for code in BLOCKING_ORDER if code in blocking_codes]
    final_status = "blocked" if ordered_codes else "done_candidate"
    return {
        "coverage_report_id": document.get("coverage_report_id", "COVERAGE-001"),
        "final_status": final_status,
        "blocking_codes": ordered_codes,
        "coverage_matrix": coverage_matrix,
        "tested_clause_ids": sorted(tested_clause_ids),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a redacted Markdown report without source text."""

    lines = [
        "# Spec Plan Coverage Report",
        "",
        f"- coverage_report_id: {report['coverage_report_id']}",
        f"- final_status: {report['final_status']}",
        f"- blocking_codes: {', '.join(report['blocking_codes']) or 'none'}",
        "",
        "| spec_clause_id | source_location | coverage_status |",
        "| --- | --- | --- |",
    ]
    for row in report["coverage_matrix"]:
        lines.append(
            "| {spec_clause_id} | {source_location} | {coverage_status} |".format(
                **row
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    report = validate_document(document)
    json_text = json.dumps(report, indent=2, sort_keys=True)
    markdown_text = render_markdown(report)
    if args.json_output:
        args.json_output.write_text(f"{json_text}\n", encoding="utf-8")
    else:
        print(json_text)
    if args.markdown_output:
        args.markdown_output.write_text(markdown_text, encoding="utf-8")
    return 0 if report["final_status"] == "done_candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
