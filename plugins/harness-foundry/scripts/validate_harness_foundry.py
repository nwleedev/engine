#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = {
    "diagnose-project",
    "design-domain-harness",
    "update-registry",
    "scaffold-domain-harness",
    "audit-domain-harness",
}
REQUIRED_BOUNDARY_PATTERNS = (
    "It does not bulk-install public awesome repositories.",
    "AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval",
    "Do not create or maintain `index.json` as a source of truth in v1.",
)


def fail(message: str) -> None:
    print(f"harness-foundry validation failed: {message}")
    sys.exit(1)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        fail("missing frontmatter")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def validate_manifest() -> None:
    path = ROOT / ".codex-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("name") != "harness-foundry":
        fail("plugin name must be harness-foundry")
    if data.get("skills") != "./skills/":
        fail("plugin skills path must be ./skills/")


def validate_skills() -> None:
    skills_dir = ROOT / "skills"
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
        if not description.startswith("Use when "):
            fail(f"{skill_name} description must start with 'Use when '")
        for heading in ("## Workflow", "## Output"):
            if heading not in text:
                fail(f"{skill_name} missing {heading}")
        if "## Do not" not in text and "## Boundaries" not in text:
            fail(f"{skill_name} missing Do not or Boundaries section")


def validate_references() -> None:
    required = {
        "domain-harness-template.md",
        "registry-template.md",
        "evaluation-template.md",
        "risk-checklist.md",
    }
    actual = {path.name for path in (ROOT / "references").glob("*.md")}
    if actual != required:
        fail(f"reference files mismatch: {sorted(actual)}")


def validate_boundary_patterns() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix in {".md", ".json", ".py"}
    )
    for pattern in REQUIRED_BOUNDARY_PATTERNS:
        if pattern not in combined:
            fail(f"missing boundary pattern: {pattern}")


def main() -> None:
    validate_manifest()
    validate_skills()
    validate_references()
    validate_boundary_patterns()
    print("harness-foundry validation passed")


if __name__ == "__main__":
    main()
