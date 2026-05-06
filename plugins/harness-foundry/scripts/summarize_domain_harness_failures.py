#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert validate_domain_harness JSON into an improvement report draft."
    )
    parser.add_argument("validation_json", help="Path to validator JSON output")
    return parser.parse_args(argv)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def group_findings(findings: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for finding in findings:
        key = finding.get("domain") or "project-wide"
        grouped[key].append(finding)
    return dict(grouped)


def render_report(payload: dict[str, Any]) -> str:
    findings = payload.get("findings", [])
    grouped = group_findings(findings)
    lines = [
        "# Domain Harness Improvement Report",
        "",
        "## Summary",
        "",
        f"- Project root: `{payload.get('root', 'unknown')}`",
        f"- Validator status: {'pass' if payload.get('ok') else 'fail'}",
        f"- Finding count: {len(findings)}",
        "",
        "## Affected harnesses",
        "",
        "| domain | findings | highest severity |",
        "|---|---|---|",
    ]
    if grouped:
        for domain, domain_findings in sorted(grouped.items()):
            severities = [finding.get("severity", "warning") for finding in domain_findings]
            highest = "error" if "error" in severities else "warning"
            lines.append(f"| {domain} | {len(domain_findings)} | {highest} |")
    else:
        lines.append("| none | 0 | none |")

    lines.extend(["", "## Findings", "", "| severity | rule_id | path | message |", "|---|---|---|---|"])
    if findings:
        for finding in findings:
            lines.append(
                "| {severity} | {rule_id} | `{path}` | {message} |".format(
                    severity=finding.get("severity", ""),
                    rule_id=finding.get("rule_id", ""),
                    path=finding.get("path", ""),
                    message=finding.get("message", "").replace("|", "\\|"),
                )
            )
    else:
        lines.append("| none | none | none | No findings. |")

    lines.extend(
        [
            "",
            "## Local fix candidates",
            "",
            "- Review each finding inside the downstream project before editing files.",
            "- Treat missing files, registry errors, and guardrail gaps as local fixes first.",
            "",
            "## Upstream regression candidates",
            "",
            "- Consider upstream contribution only after the case is reduced to public-safe synthetic content.",
            "- Candidate rule ids: "
            + (", ".join(sorted({finding.get("rule_id", "") for finding in findings})) or "none"),
            "",
            "## Privacy and sanitization review",
            "",
            "- `privacy_sanitization_check`: not yet reviewed",
            "- Confirm that secrets, credentials, customer data, private source code, and internal documents are absent before sharing.",
            "",
            "## Verification checklist",
            "",
            "- [ ] Re-run `validate_domain_harness.py` after local fixes.",
            "- [ ] Confirm report contents are public-safe before upstream sharing.",
            "- [ ] Assign owners for unresolved findings.",
            "",
            "## Open questions",
            "",
            "- None recorded.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    path = Path(args.validation_json)
    if not path.is_file():
        print(f"unreadable validation json: {path}", file=sys.stderr)
        return 2
    print(render_report(load_payload(path)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
