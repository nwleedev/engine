from pathlib import Path
from typing import Any


def parse_frontmatter(content: str) -> dict[str, Any]:
    if not content.startswith("---"):
        return {}
    end = content.find("\n---\n", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("["):
            items = [x.strip().strip('"\'') for x in val.strip("[]").split(",")]
            result[key.strip()] = [x for x in items if x]
        else:
            result[key.strip()] = val
    return result


def has_harness_dir(project_root: str) -> bool:
    return (Path(project_root) / ".claude" / "harness").is_dir()


def read_harness_files(harness_dir: str) -> list[dict[str, Any]]:
    path = Path(harness_dir)
    if not path.exists():
        return []
    files = []
    for md_file in sorted(path.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            files.append({
                "path": str(md_file),
                "domain": fm.get("domain", md_file.stem),
                "domain_type": fm.get("domain_type", "code"),
                "languages": fm.get("languages", []),
                "frameworks": fm.get("frameworks", []),
                "linters": fm.get("linters", []),
                "file_patterns": fm.get("file_patterns", []),
                "keywords": fm.get("keywords", []),
                "updated": fm.get("updated", ""),
                "content": content,
            })
        except OSError:
            continue
    return files


def write_harness_file(harness_dir: str, domain: str, content: str) -> str:
    path = Path(harness_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{domain}.md"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def harness_file_exists(harness_dir: str, domain: str) -> bool:
    return (Path(harness_dir) / f"{domain}.md").exists()


def read_all_harness_content(harness_dir: str) -> str:
    files = read_harness_files(harness_dir)
    if not files:
        return ""
    parts = [f"## Domain: {f['domain']}\n\n{f['content']}" for f in files]
    return "\n\n---\n\n".join(parts)
