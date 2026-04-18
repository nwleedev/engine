import fnmatch
import os
from pathlib import Path


def parse_harness_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("["):
            items = [x.strip().strip('"\'') for x in val.strip("[]").split(",")]
            result[key.strip()] = [x for x in items if x]
        else:
            result[key.strip()] = val.strip('"\'')
    return result


def load_harness_files(harness_dir: Path) -> list[dict]:
    files = []
    if not harness_dir.exists():
        return files
    for path in sorted(harness_dir.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
            fm = parse_harness_frontmatter(content)
            files.append({
                "path": path,
                "content": content,
                "domain": fm.get("domain", path.stem),
                "keywords": fm.get("keywords", []),
                "language": fm.get("language", "auto"),
                "file_patterns": fm.get("file_patterns", []),
            })
        except OSError:
            continue
    return files


def detect_domains_from_prompt(prompt: str, harness_files: list[dict]) -> list[dict]:
    prompt_lower = prompt.lower()
    matched = [f for f in harness_files if any(kw.lower() in prompt_lower for kw in f["keywords"])]
    return matched[:3]


def _matches_pattern(file_path: str, pattern: str) -> bool:
    fp = file_path.replace("\\", "/")
    if "**" not in pattern:
        return fnmatch.fnmatch(fp, pattern) or fnmatch.fnmatch(os.path.basename(fp), pattern)
    before, _, after = pattern.partition("**")
    prefix = before.rstrip("/")
    suffix = after.lstrip("/")
    if prefix and not (fp.startswith(prefix + "/") or fp == prefix):
        return False
    if not suffix:
        return True
    if fnmatch.fnmatch(os.path.basename(fp), suffix):
        return True
    return fnmatch.fnmatch(fp, f"*/{suffix}") or fnmatch.fnmatch(fp, suffix)


def detect_domain_from_file_path(file_path: str, harness_files: list[dict]) -> dict | None:
    for f in harness_files:
        for pattern in f.get("file_patterns", []):
            if _matches_pattern(file_path, pattern):
                return f
    return None
