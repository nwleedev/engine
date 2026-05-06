#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(
    sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
).resolve()
SKILL_NAMES = {
    "diagnose-project",
    "design-domain-harness",
    "update-registry",
    "scaffold-domain-harness",
    "audit-domain-harness",
}
MANIFEST_KEYS = {"name", "version", "description", "license", "skills"}
FORBIDDEN_PLUGIN_FILES = (
    ".app.json",
    ".mcp.json",
    "hooks/hooks.json",
)
REFERENCE_FILES = {
    "domain-harness-template.md",
    "registry-template.md",
    "evaluation-template.md",
    "risk-checklist.md",
    "domain-harness-eval-metrics.md",
    "improvement-report-template.md",
    "sanitized-regression-case-template.md",
    "downstream-issue-template.md",
    "downstream-adoption-guide.md",
}
SCRIPT_FILES = {
    "validate_harness_foundry.py",
    "validate_domain_harness.py",
    "summarize_domain_harness_failures.py",
}
ISSUE_TEMPLATE_FILES = {
    "harness-quality-issue.yml",
    "upstream-regression-case.yml",
    "harness-feature-request.yml",
    "config.yml",
}
FIXTURE_DIRS = {
    "valid-dev",
    "valid-nondev",
    "valid-mixed",
    "invalid-missing-registry",
    "invalid-missing-spec",
    "invalid-missing-evals",
    "invalid-index-json-source",
    "invalid-auto-hooks",
    "invalid-auto-mcp",
    "invalid-nondev-no-source-policy",
    "invalid-mixed-no-split-guardrails",
}


def fail(message: str) -> None:
    print(f"harness-foundry validation failed: {message}")
    sys.exit(1)


def parse_frontmatter(text: str) -> dict[str, str | dict[str, str]]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        fail("missing frontmatter")
    result: dict[str, str | dict[str, str]] = {}
    current_parent: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                result[key] = value
                current_parent = None
            else:
                result[key] = {}
                current_parent = key
        elif current_parent and ":" in line and line.startswith(" "):
            key, value = line.split(":", 1)
            parent = result[current_parent]
            if isinstance(parent, dict):
                parent[key.strip()] = value.strip().strip('"')
    return result


def validate_manifest() -> None:
    path = ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        fail("missing required file: .codex-plugin/plugin.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    missing_keys = MANIFEST_KEYS - set(data)
    if missing_keys:
        fail(f"plugin manifest missing required keys: {sorted(missing_keys)}")
    extra_keys = set(data) - MANIFEST_KEYS
    if extra_keys:
        fail(f"plugin manifest has non-v1 keys: {sorted(extra_keys)}")
    if data.get("name") != "harness-foundry":
        fail("plugin name must be harness-foundry")
    if data.get("skills") != "./skills/":
        fail("plugin skills path must be ./skills/")
    for relative_path in FORBIDDEN_PLUGIN_FILES:
        if (ROOT / relative_path).exists():
            fail(f"v1 skill-only plugin must not include {relative_path}")


def validate_skills() -> None:
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        fail("missing required directory: skills")
    actual = {path.name for path in skills_dir.iterdir() if path.is_dir()}
    if actual != SKILL_NAMES:
        fail(f"skill directories mismatch: {sorted(actual)}")

    for skill_name in sorted(SKILL_NAMES):
        path = skills_dir / skill_name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        if frontmatter.get("name") != skill_name:
            fail(f"{skill_name} frontmatter name mismatch")
        description = frontmatter.get("description", "")
        if not isinstance(description, str) or not description.startswith("Use when "):
            fail(f"{skill_name} description must start with 'Use when '")
        metadata = frontmatter.get("metadata")
        if not isinstance(metadata, dict) or not metadata.get("short-description"):
            fail(f"{skill_name} missing metadata.short-description")
        for heading in ("## Workflow", "## Output"):
            if heading not in text:
                fail(f"{skill_name} missing {heading}")
        if "## Do not" not in text and "## Boundaries" not in text:
            fail(f"{skill_name} missing Do not or Boundaries section")


def validate_references() -> None:
    actual = {path.name for path in (ROOT / "references").glob("*.md")}
    if actual != REFERENCE_FILES:
        fail(f"reference files mismatch: {sorted(actual)}")


def validate_scripts_assets_and_fixtures() -> None:
    actual_scripts = {path.name for path in (ROOT / "scripts").glob("*.py")}
    if actual_scripts != SCRIPT_FILES:
        fail(f"script files mismatch: {sorted(actual_scripts)}")

    issue_template_dir = ROOT / "assets" / "github-templates" / "ISSUE_TEMPLATE"
    actual_issue_templates = {path.name for path in issue_template_dir.glob("*.yml")}
    if actual_issue_templates != ISSUE_TEMPLATE_FILES:
        fail(f"issue template files mismatch: {sorted(actual_issue_templates)}")
    if not (ROOT / "assets" / "github-templates" / "pull_request_template.md").is_file():
        fail("missing required file: assets/github-templates/pull_request_template.md")

    fixture_root = ROOT / "fixtures" / "domain-harness"
    actual_fixtures = {path.name for path in fixture_root.iterdir() if path.is_dir()}
    if actual_fixtures != FIXTURE_DIRS:
        fail(f"domain harness fixture directories mismatch: {sorted(actual_fixtures)}")
    for fixture_name in sorted(FIXTURE_DIRS):
        if not (fixture_root / fixture_name / "fixture.json").is_file():
            fail(f"fixture missing fixture.json: {fixture_name}")


def validate_boundary_patterns() -> None:
    required_by_file = {
        "README.md": (
            "It does not bulk-install public awesome repositories.",
            "It supports development, non-development, and mixed work.",
            "Downstream reports are project-local artifacts.",
            "Operator-run",
        ),
        "README.ko.md": (
            "영어 README와 `SKILL.md`가 canonical 문서",
            "공개 skills/subagents를 대량 설치하는 도구가 아니라",
            "현업 프로젝트의 report는 project-local 산출물",
            "현업 프로젝트의 report는 자동 저장하지 않습니다",
        ),
        "skills/diagnose-project/SKILL.md": (
            "Do not recommend bulk-installing public awesome repositories.",
        ),
        "skills/scaffold-domain-harness/SKILL.md": (
            "AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval",
            "GitHub issue and PR templates require separate explicit approval",
            "docs/domain-harness/** files require explicit approval",
        ),
        "skills/audit-domain-harness/SKILL.md": (
            "privacy_sanitization_check",
            "validate_domain_harness.py",
            "local harness issue",
        ),
        "references/downstream-adoption-guide.md": (
            "Operator-run is the default v1 adoption model.",
            "GitHub issue and PR templates remain passive assets until explicit approval.",
            "Separate local fixes from upstream regression candidates.",
        ),
        "skills/update-registry/SKILL.md": (
            "Do not create or maintain `index.json` as a source of truth in v1.",
        ),
    }
    for relative_path, patterns in required_by_file.items():
        path = ROOT / relative_path
        if not path.exists():
            fail(f"missing required file: {relative_path}")
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern not in text:
                fail(f"{relative_path} missing boundary pattern: {pattern}")


def main() -> None:
    validate_manifest()
    validate_skills()
    validate_references()
    validate_scripts_assets_and_fixtures()
    validate_boundary_patterns()
    print("harness-foundry validation passed")


if __name__ == "__main__":
    main()
