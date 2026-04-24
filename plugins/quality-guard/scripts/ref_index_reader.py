from pathlib import Path


def read_index(cwd: str) -> str:
    path = Path(cwd) / ".claude" / "refs" / "INDEX.md"
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
