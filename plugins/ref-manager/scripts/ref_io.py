from __future__ import annotations

import re
from pathlib import Path


def get_refs_dir(cwd: str) -> Path:
    return Path(cwd) / ".claude" / "refs"


def get_index_path(cwd: str) -> Path:
    return get_refs_dir(cwd) / "INDEX.md"


def load_index(cwd: str) -> list[dict]:
    index_path = get_index_path(cwd)
    if not index_path.exists():
        return []

    entries: list[dict] = []
    content = index_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*[-:]+", line):
            continue
        if "Name" in line and "Path" in line and "Tags" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        name, path, tags_raw = parts[0], parts[1], parts[2]
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw.strip() else []
        entries.append({"name": name, "path": path, "tags": tags})
    return entries


def save_index(cwd: str, entries: list[dict]) -> None:
    index_path = get_index_path(cwd)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Refs Index",
        "",
        "| Name | Path | Tags |",
        "|---|---|---|",
    ]
    for entry in entries:
        name = entry.get("name", "")
        path = entry.get("path", "")
        tags = entry.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""
        lines.append(f"| {name} | {path} | {tags_str} |")

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_entry(cwd: str, name: str, rel_path: str, tags: list[str]) -> None:
    entries = load_index(cwd)
    entries.append({"name": name, "path": rel_path, "tags": tags})
    save_index(cwd, entries)
