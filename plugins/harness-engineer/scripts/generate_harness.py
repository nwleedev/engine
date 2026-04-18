import os
from datetime import date
from pathlib import Path


_DOMAIN_DETECTION_RULES = [
    (["*.tsx", "*.jsx"], "react-frontend"),
    (["*.py"], "python-backend"),
    (["*.go"], "go-backend"),
    (["*.ts"], "typescript"),
]

_RESEARCH_DIR_PATTERNS = ["research", "market", "competitive"]


def detect_project_domains(project_root: str) -> list[str]:
    root = Path(project_root)
    found: set[str] = set()

    for pattern, domain in _DOMAIN_DETECTION_RULES:
        for glob in pattern:
            if list(root.rglob(glob)):
                found.add(domain)
                break

    for d in root.rglob("*"):
        if d.is_dir() and any(p in d.name.lower() for p in _RESEARCH_DIR_PATTERNS):
            found.add("market-research")
            break

    return sorted(found)


def get_template(domain: str, plugin_root: str) -> str:
    template_path = Path(plugin_root) / "skills" / "harness-engineer" / "templates" / f"{domain}.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return f"""---
domain: {domain}
language: auto
keywords: []
updated: {date.today().strftime("%Y-%m-%d")}
---

# {domain.replace("-", " ").title()} Harness

## 핵심 규칙

- [ ] (이 도메인의 핵심 규칙을 작성하세요)

## 패턴 사례

<Good>
(좋은 패턴 예시)
</Good>

<Bad>
(나쁜 패턴 예시)
</Bad>

## 안티패턴 게이트

```
(편집 전 자문할 질문을 작성하세요)
```
"""


def build_harness_frontmatter(domain: str, language: str) -> str:
    today = date.today().strftime("%Y-%m-%d")
    return f"---\ndomain: {domain}\nlanguage: {language}\nupdated: {today}\n---"


def generate_harness_file(
    domain: str,
    project_root: str,
    language: str,
    plugin_root: str,
) -> str:
    template = get_template(domain, plugin_root)
    if template.startswith("---"):
        end = template.find("---", 3)
        if end != -1:
            body = template[end + 3:]
            new_fm = build_harness_frontmatter(domain, language)
            return new_fm + body
    return build_harness_frontmatter(domain, language) + "\n\n" + template
