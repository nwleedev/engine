import os
from datetime import date
from pathlib import Path


def get_template(domain: str, plugin_root: str) -> str:
    template_path = Path(plugin_root) / "skills" / "harness-engineer" / "templates" / f"{domain}.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return f"""---
domain: {domain}
language: auto
keywords: []
file_patterns: []
updated: {date.today().strftime("%Y-%m-%d")}
---

# {domain.replace("-", " ").title()} Harness

## Purpose
Define the ideal standard for this domain, not the current project state.

## Core Rules

- [ ] (Add core rules for this domain)

## Pattern Examples

<Good>
(Good pattern example)
</Good>

<Bad>
(Bad pattern example)
</Bad>

## Anti-Pattern Gate

```
(Questions to ask before editing)
```
"""


def build_harness_frontmatter(
    domain: str,
    language: str,
    keywords: list[str] | None = None,
    file_patterns: list[str] | None = None,
    domain_type: str = "code",
) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"domain: {domain}",
        f"domain_type: {domain_type}",
        f"language: {language}",
    ]
    if keywords is not None:
        kw_str = ", ".join(keywords)
        lines.append(f"keywords: [{kw_str}]")
    if file_patterns is not None:
        quoted = [f'"{p}"' for p in file_patterns]
        lines.append(f"file_patterns: [{', '.join(quoted)}]")
    lines.append(f"updated: {today}")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter_list(template: str, field: str) -> list[str]:
    if not template.startswith("---"):
        return []
    end = template.find("---", 3)
    if end == -1:
        return []
    fm_text = template[3:end].strip()
    for line in fm_text.splitlines():
        key, _, val = line.partition(":")
        if key.strip() == field:
            val = val.strip()
            if val.startswith("["):
                items = [x.strip().strip('"\'') for x in val.strip("[]").split(",")]
                return [x for x in items if x]
    return []


def _parse_frontmatter_str(template: str, field: str, default: str = "") -> str:
    if not template.startswith("---"):
        return default
    end = template.find("---", 3)
    if end == -1:
        return default
    fm_text = template[3:end].strip()
    for line in fm_text.splitlines():
        key, _, val = line.partition(":")
        if key.strip() == field:
            return val.strip().strip('"\'') or default
    return default


def generate_harness_file(
    domain: str,
    project_root: str,
    language: str,
    plugin_root: str,
) -> str:
    template = get_template(domain, plugin_root)
    keywords = _parse_frontmatter_list(template, "keywords")
    file_patterns = _parse_frontmatter_list(template, "file_patterns")
    domain_type = _parse_frontmatter_str(template, "domain_type", "code")
    if template.startswith("---"):
        end = template.find("---", 3)
        if end != -1:
            body = template[end + 3:]
            new_fm = build_harness_frontmatter(domain, language, keywords, file_patterns, domain_type)
            return new_fm + body
    return build_harness_frontmatter(domain, language, keywords, file_patterns, domain_type) + "\n\n" + template


def _extract_section(content: str, header: str) -> str:
    """Extract a ## section body from markdown. Returns empty string if not found."""
    lines = content.splitlines()
    in_section = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped == header or stripped.startswith(header + " "):
            in_section = True
            result.append(line)
            continue
        if in_section:
            if stripped.startswith("## ") and not (stripped == header or stripped.startswith(header + " ")):
                break
            result.append(line)
    return "\n".join(result).strip()


def generate_skill_file(domain: str, harness_content: str, project_root: str) -> str:
    """
    Derive a standalone SKILL.md from a harness file.
    Extracts ## Core Rules and ## Anti-Pattern Gate.
    Writes to <project_root>/.claude/skills/<domain>-harness/SKILL.md.
    Returns the absolute path of the written file.
    """
    core_rules = _extract_section(harness_content, "## Core Rules")
    anti_pattern_gate = _extract_section(harness_content, "## Anti-Pattern Gate")
    display_name = domain.replace("-", " ").title()
    description = (
        f"This skill should be used when the user is working on "
        f"{display_name.lower()} tasks. "
        f"Activates quality enforcement rules for {display_name.lower()} output."
    )
    skill_content = (
        f"---\n"
        f"name: {domain}-harness\n"
        f"description: {description}\n"
        f"---\n\n"
        f"# {display_name} Harness\n\n"
        f"Enforce the following quality standards throughout this work session.\n"
        f"Before accepting any claim or output, run through the Anti-Pattern Gate.\n\n"
        f"{core_rules}\n\n"
        f"{anti_pattern_gate}\n"
    )
    skill_dir = Path(project_root) / ".claude" / "skills" / f"{domain}-harness"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    return str(skill_path)
