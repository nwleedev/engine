"""v1 → v2 data migration. Invoked by /session-memory:migrate."""
import re
from pathlib import Path

import index_io

ENTRY_RE = re.compile(r"^- \[([^\]]+)\] — (.*)$", re.MULTILINE)


def dedup_index(session_dir: "str | Path", dry_run: bool = True) -> bool:
    """Collapse duplicate [filename] entries to the latest one_liner. Returns True if changed."""
    p = Path(session_dir) / "INDEX.md"
    if not p.exists():
        return False
    content = p.read_text(encoding="utf-8")
    fm, body = index_io.parse_frontmatter(content)

    last_one_liner: dict = {}
    order: list = []
    for line in body.split("\n"):
        m = ENTRY_RE.match(line)
        if m:
            fn, ol = m.group(1), m.group(2)
            if fn not in last_one_liner:
                order.append(fn)
            last_one_liner[fn] = ol

    new_entries = [f"- [{fn}] — {last_one_liner[fn]}" for fn in order]
    if not new_entries:
        return False

    new_body_lines = []
    inserted = False
    for line in body.split("\n"):
        if ENTRY_RE.match(line):
            if not inserted:
                new_body_lines.extend(new_entries)
                inserted = True
            continue
        new_body_lines.append(line)
    if not inserted:
        new_body_lines.extend(new_entries)

    new_body = "\n".join(new_body_lines)
    if new_body == body:
        return False
    if dry_run:
        return True
    index_io.atomic_write(p, index_io.serialize(fm, new_body))
    return True


def dedup_all_sessions(sessions_dir: "str | Path", dry_run: bool = True) -> dict:
    """Run dedup_index on every session. Returns {session_id: changed_bool}."""
    out = {}
    for s in Path(sessions_dir).iterdir():
        if not s.is_dir() or s.name.startswith("_") or s.name.startswith("."):
            continue
        out[s.name] = dedup_index(s, dry_run=dry_run)
    return out
