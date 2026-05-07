#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PLUGIN_ROOT = REPO_ROOT / "plugins" / "harness-foundry"
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
}
SKILL_LOCAL_SCRIPT_FILES = {
    "skills/audit-domain-harness/scripts/validate_domain_harness.py",
}


def fail(message: str) -> None:
    print(f"harness-foundry plugin package validation failed: {message}")
    sys.exit(1)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the harness-foundry public plugin package boundary."
    )
    parser.add_argument(
        "plugin_root",
        nargs="?",
        default=DEFAULT_PLUGIN_ROOT,
        type=lambda value: Path(value).resolve(),
        help="Path to the plugin root. Defaults to plugins/harness-foundry.",
    )
    args = parser.parse_args(argv)
    args.plugin_root = Path(args.plugin_root).resolve()
    return args


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


def validate_manifest(root: Path) -> None:
    path = root / ".codex-plugin" / "plugin.json"
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
        if (root / relative_path).exists():
            fail(f"v1 skill-only plugin must not include {relative_path}")


def validate_skills(root: Path) -> None:
    skills_dir = root / "skills"
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


def validate_references(root: Path) -> None:
    actual = {path.name for path in (root / "references").glob("*.md")}
    if actual != REFERENCE_FILES:
        fail(f"reference files mismatch: {sorted(actual)}")


def validate_scripts(root: Path) -> None:
    if (root / "scripts").exists():
        fail("plugin root must not include scripts directory")
    if (root / "tests").exists():
        fail("plugin root must not include tests directory")

    missing_skill_scripts = [
        relative_path
        for relative_path in sorted(SKILL_LOCAL_SCRIPT_FILES)
        if not (root / relative_path).is_file()
    ]
    if missing_skill_scripts:
        fail(f"missing required skill-local script files: {missing_skill_scripts}")


def validate_boundary_patterns(root: Path) -> None:
    required_by_file = {
        "README.md": (
            "It does not bulk-install public awesome repositories.",
            "It supports development, non-development, and mixed work.",
            "explicit user approval",
        ),
        "README.ko.md": (
            "영어 README와 `SKILL.md`가 canonical 문서",
            "공개 skills/subagents를 대량 설치하는 도구가 아니라",
            "사용자 명시 승인",
        ),
        "skills/diagnose-project/SKILL.md": (
            "Do not recommend bulk-installing public awesome repositories.",
        ),
        "skills/scaffold-domain-harness/SKILL.md": (
            "AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval",
            "docs/domain-harness/** files require explicit approval",
        ),
        "skills/audit-domain-harness/SKILL.md": (
            "Perform a read-only audit",
            "Findings ordered by severity",
        ),
        "skills/update-registry/SKILL.md": (
            "Do not create or maintain `index.json` as a source of truth in v1.",
        ),
    }
    for relative_path, patterns in required_by_file.items():
        path = root / relative_path
        if not path.exists():
            fail(f"missing required file: {relative_path}")
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern not in text:
                fail(f"{relative_path} missing boundary pattern: {pattern}")


def validate_plugin_package(root: Path) -> None:
    validate_manifest(root)
    validate_skills(root)
    validate_references(root)
    validate_scripts(root)
    validate_boundary_patterns(root)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    validate_plugin_package(args.plugin_root)
    print("harness-foundry plugin package validation passed")


if __name__ == "__main__":
    main()
