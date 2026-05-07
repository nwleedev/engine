#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_VALIDATOR_PATH = (
    REPO_ROOT
    / "plugins"
    / "harness-foundry"
    / "skills"
    / "audit-domain-harness"
    / "scripts"
    / "validate_domain_harness.py"
)


def load_base_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_harness_foundry_domain_validator", BASE_VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load base validator: {BASE_VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE_VALIDATOR = load_base_validator()
Finding = BASE_VALIDATOR.Finding
relative_path = BASE_VALIDATOR.relative_path
render_human = BASE_VALIDATOR.render_human
validate_base_project = BASE_VALIDATOR.validate_project


def unreadable_public_safety_finding(path: Path, root: Path) -> Finding:
    return Finding(
        "unreadable-public-safety-artifact",
        "warning",
        relative_path(path, root),
        "Public-safety artifact candidate is not a readable UTF-8 file.",
    )


def validate_public_safety_reviews(harness_root: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    candidates = sorted((harness_root / "evaluation-reports").glob("*.md"))
    candidates.extend(sorted((harness_root / "sanitized-evaluation-cases").glob("*.md")))
    for path in candidates:
        if not path.is_file():
            findings.append(unreadable_public_safety_finding(path, root))
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            findings.append(unreadable_public_safety_finding(path, root))
            continue
        if "public_safety_check" not in text and "public-safety review" not in text:
            findings.append(
                Finding(
                    "missing-public-safety-check",
                    "warning",
                    relative_path(path, root),
                    "Evaluation report or sanitized evaluation case must include public_safety_check or equivalent public-safety review.",
                )
            )
    return findings


def validate_project(root: Path) -> list[Finding]:
    harness_root = root / "docs" / "domain-harness"
    findings = validate_base_project(root)
    findings.extend(validate_public_safety_reviews(harness_root, root))
    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate domain-harness evaluation corpus artifacts.")
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
