import re
from datetime import datetime, timezone
from pathlib import Path


_CHECKPOINT_RE = re.compile(r'<!--\s*checkpoint:\s*(\S+)\s*-->')
_ENTRY_RE = re.compile(r'---\nts:\s*(\S+)\ntext:\s*"([^"\\]*(?:\\.[^"\\]*)*)"\n---')


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _raw_path(cwd: str) -> Path:
    return Path(cwd) / ".claude" / "feedback" / "raw.md"


def _rules_path(cwd: str) -> Path:
    return Path(cwd) / ".claude" / "feedback" / "rules.md"


def load_raw_since_checkpoint(cwd: str) -> list[str]:
    """Return text values of raw.md entries newer than the checkpoint timestamp."""
    path = _raw_path(cwd)
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    m = _CHECKPOINT_RE.search(content)
    checkpoint = m.group(1) if m else ""
    entries = []
    for ts, text in _ENTRY_RE.findall(content):
        if not checkpoint or ts > checkpoint:
            entries.append(text.replace('\\"', '"'))
    return entries


def append_raw_entry(cwd: str, text: str) -> None:
    """Append a new entry to raw.md. Create the file with a checkpoint header if absent."""
    if not text:
        return
    path = _raw_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("<!-- checkpoint: 1970-01-01T00:00:00Z -->\n", encoding="utf-8")
    ts = _utcnow_iso()
    escaped = text.replace('"', '\\"')
    entry = f'\n---\nts: {ts}\ntext: "{escaped}"\n---\n'
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)


def reset_raw_md(cwd: str) -> None:
    """Clear all entries from raw.md and update the checkpoint to now."""
    path = _raw_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<!-- checkpoint: {_utcnow_iso()} -->\n", encoding="utf-8")


def load_feedback_rules(cwd: str) -> str:
    """Return the content of rules.md, or empty string if absent."""
    path = _rules_path(cwd)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def increment_pending_review(cwd: str, amount: int) -> None:
    """Increment .claude/quality/pending_review.txt by `amount`. Creates file if missing."""
    if amount <= 0:
        return
    path = Path(cwd) / ".claude" / "quality" / "pending_review.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = 0
    if path.exists():
        try:
            existing = int(path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing = 0
    path.write_text(str(existing + amount), encoding="utf-8")
