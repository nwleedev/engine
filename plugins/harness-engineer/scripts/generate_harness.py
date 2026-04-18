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
) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"domain: {domain}",
        f"language: {language}",
    ]
    if keywords:
        kw_str = ", ".join(keywords)
        lines.append(f"keywords: [{kw_str}]")
    if file_patterns:
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


def generate_harness_file(
    domain: str,
    project_root: str,
    language: str,
    plugin_root: str,
) -> str:
    template = get_template(domain, plugin_root)
    keywords = _parse_frontmatter_list(template, "keywords")
    file_patterns = _parse_frontmatter_list(template, "file_patterns")
    if template.startswith("---"):
        end = template.find("---", 3)
        if end != -1:
            body = template[end + 3:]
            new_fm = build_harness_frontmatter(domain, language, keywords, file_patterns)
            return new_fm + body
    return build_harness_frontmatter(domain, language, keywords, file_patterns) + "\n\n" + template
