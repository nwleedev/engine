#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = (
    "domain",
    "work_type",
    "status",
    "owner",
    "spec",
    "evals",
    "scaffold",
    "last_reviewed",
)
VALID_WORK_TYPES = {"development", "non-development", "mixed"}
VALID_STATUSES = {"draft", "active", "deprecated"}
ACTIVE_STATUSES = {"active"}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    message: str
    domain: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "domain": self.domain,
        }


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_text_or_finding(
    path: Path, root: Path, rule_id: str, message: str, domain: str = ""
) -> tuple[str | None, Finding | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeDecodeError):
        return None, Finding(rule_id, "error", relative_path(path, root), message, domain)


def parse_registry(index_path: Path, root: Path) -> tuple[list[dict[str, str]], list[Finding]]:
    text, finding = read_text_or_finding(
        index_path,
        root,
        "unreadable-registry",
        "Registry file must be a readable UTF-8 Markdown file.",
    )
    if finding is not None:
        return [], [finding]
    assert text is not None
    lines = text.splitlines()
    tables: list[list[str]] = []
    current_table: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            current_table.append(line)
            continue
        if current_table:
            tables.append(current_table)
            current_table = []
    if current_table:
        tables.append(current_table)

    table_lines = tables[0] if tables else []
    if len(table_lines) < 2:
        return [], [
            Finding(
                "registry-parse-error",
                "error",
                relative_path(index_path, root),
                "Registry must contain a Markdown pipe table.",
            )
        ]

    headers = [clean_cell(cell) for cell in table_lines[0].strip().strip("|").split("|")]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing_columns:
        return [], [
            Finding(
                "registry-parse-error",
                "error",
                relative_path(index_path, root),
                f"Registry table missing columns: {', '.join(missing_columns)}.",
            )
        ]

    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [clean_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            return [], [
                Finding(
                    "registry-parse-error",
                    "error",
                    relative_path(index_path, root),
                    "Registry row cell count does not match header count.",
                )
            ]
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows, []


def contains_all(text: str, required_patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(pattern in lowered for pattern in required_patterns)


def validate_work_type_guardrails(
    work_type: str, spec_path: Path, root: Path, domain: str
) -> list[Finding]:
    if not spec_path.is_file():
        return []
    text, finding = read_text_or_finding(
        spec_path,
        root,
        "unreadable-harness-artifact",
        "Harness artifact must be a readable UTF-8 Markdown file.",
        domain,
    )
    if finding is not None:
        return [finding]
    assert text is not None
    rel = relative_path(spec_path, root)
    findings: list[Finding] = []
    if work_type == "development" and not contains_all(
        text,
        ("implementation scope", "test strategy", "security review", "dependency"),
    ):
        findings.append(
            Finding(
                "missing-development-guardrails",
                "error",
                rel,
                "Development harness must include implementation, test, security, and dependency guardrails.",
                domain,
            )
        )
    if work_type == "non-development" and not contains_all(
        text,
        ("source quality", "privacy", "tone", "approval flow"),
    ):
        findings.append(
            Finding(
                "missing-non-development-source-policy",
                "error",
                rel,
                "Non-development harness must include source quality, privacy, tone, and approval flow guardrails.",
                domain,
            )
        )
    if work_type == "mixed":
        has_dev = contains_all(
            text,
            ("development guardrails", "implementation scope", "test strategy", "security review"),
        )
        has_nondev = contains_all(
            text,
            ("non-development guardrails", "source quality", "privacy", "approval flow"),
        )
        has_split = "mixed split guardrails" in text.lower()
        if not (has_dev and has_nondev and has_split):
            findings.append(
                Finding(
                    "missing-mixed-split-guardrails",
                    "error",
                    rel,
                    "Mixed harness must explicitly split development and non-development guardrails.",
                    domain,
                )
            )
    return findings


def detect_unapproved_activation(path: Path, root: Path, domain: str) -> list[Finding]:
    if not path.is_file():
        return []
    text, finding = read_text_or_finding(
        path,
        root,
        "unreadable-harness-artifact",
        "Harness artifact must be a readable UTF-8 Markdown file.",
        domain,
    )
    if finding is not None:
        return [finding]
    assert text is not None
    text = text.lower()
    rel = relative_path(path, root)
    findings: list[Finding] = []
    if re.search(r"automatically\s+(activate|enable|install).{0,40}hooks?", text):
        findings.append(
            Finding(
                "unapproved-auto-hooks",
                "error",
                rel,
                "Harness artifact plans hook activation without explicit approval.",
                domain,
            )
        )
    if re.search(r"automatically\s+(activate|enable|install).{0,40}mcp", text):
        findings.append(
            Finding(
                "unapproved-auto-mcp",
                "error",
                rel,
                "Harness artifact plans MCP activation without explicit approval.",
                domain,
            )
        )
    return findings


def validate_project(root: Path) -> list[Finding]:
    harness_root = root / "docs" / "domain-harness"
    index_path = harness_root / "index.md"
    if not index_path.is_file():
        return [
            Finding(
                "missing-registry",
                "error",
                relative_path(index_path, root),
                "Missing docs/domain-harness/index.md registry.",
            )
        ]

    rows, findings = parse_registry(index_path, root)

    index_json = harness_root / "index.json"
    if index_json.exists():
        findings.append(
            Finding(
                "index-json-source-of-truth",
                "error",
                relative_path(index_json, root),
                "v1 must not use index.json as the domain harness source of truth.",
            )
        )

    for row in rows:
        status = row.get("status", "")
        domain = row.get("domain", "")
        if status not in VALID_STATUSES:
            findings.append(
                Finding(
                    "invalid-status",
                    "error",
                    relative_path(index_path, root),
                    f"Invalid status for domain {domain}: {status}.",
                    domain,
                )
            )
            continue
        if status not in ACTIVE_STATUSES:
            continue
        work_type = row.get("work_type", "")
        if work_type not in VALID_WORK_TYPES:
            findings.append(
                Finding(
                    "invalid-work-type",
                    "error",
                    relative_path(index_path, root),
                    f"Invalid work_type for domain {domain}: {work_type}.",
                    domain,
                )
            )
            continue

        artifact_refs = {
            "missing-spec-file": row.get("spec", ""),
            "missing-evals-file": row.get("evals", ""),
            "missing-scaffold-file": row.get("scaffold", ""),
        }
        paths: dict[str, Path] = {}
        for rule_id, artifact_ref in artifact_refs.items():
            if not artifact_ref:
                findings.append(
                    Finding(
                        rule_id,
                        "error",
                        relative_path(index_path, root),
                        f"Active registry row for {domain} has an empty registry value.",
                        domain,
                    )
                )
                continue
            paths[rule_id] = harness_root / artifact_ref
        for rule_id, path in paths.items():
            if not path.is_file():
                findings.append(
                    Finding(
                        rule_id,
                        "error",
                        relative_path(path, root),
                        f"Active registry row for {domain} points to a missing file.",
                        domain,
                    )
                )

        spec_path = paths.get("missing-spec-file")
        unreadable_paths: set[Path] = set()
        if spec_path is not None:
            spec_findings = validate_work_type_guardrails(work_type, spec_path, root, domain)
            findings.extend(spec_findings)
            if any(finding.rule_id == "unreadable-harness-artifact" for finding in spec_findings):
                unreadable_paths.add(spec_path)
        for artifact_path in paths.values():
            if artifact_path in unreadable_paths:
                continue
            findings.extend(detect_unapproved_activation(artifact_path, root, domain))

    return findings


def render_human(root: Path, findings: list[Finding]) -> str:
    if not findings:
        return "domain harness validation passed\n"
    has_errors = any(finding.severity == "error" for finding in findings)
    lines = [
        "domain harness validation failed"
        if has_errors
        else "domain harness validation passed with warnings"
    ]
    for finding in findings:
        lines.append(
            f"- [{finding.severity}] {finding.rule_id} {finding.path}: {finding.message}"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate project-local domain harness artifacts.")
    parser.add_argument("project_root", help="Root containing docs/domain-harness/index.md")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"unreadable project root: {root}", file=sys.stderr)
        return 2

    findings = validate_project(root)
    payload = {
        "ok": not any(finding.severity == "error" for finding in findings),
        "root": str(root),
        "findings": [finding.to_dict() for finding in findings],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_human(root, findings), end="")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
