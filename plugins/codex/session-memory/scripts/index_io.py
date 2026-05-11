"""INDEX.md frontmatter + body manipulation. Stdlib only.

YAML subset: KEY: VALUE per line, integer/string scalars only.
Body has stable section: '## Contexts' followed by '- [filename.md] — summary' lines.
"""
from pathlib import Path
from typing import Any


_FENCE = "---"
_CONTEXT_HEADING = "## Contexts"
_RESUME_HINT = "Resume this session: `$session-memory:resume {session_prefix}`"


def _coerce(v: str):
    s = v.strip()
    if s.lstrip("-").isdigit():
        try:
            return int(s)
        except ValueError:
            pass
    return s


def read_frontmatter(path: Path):
    p = Path(path)
    if not p.is_file():
        return None
    text = p.read_text()
    if not text.startswith(_FENCE):
        return {}
    end = text.find("\n" + _FENCE, len(_FENCE))
    if end < 0:
        return {}
    block = text[len(_FENCE):end].strip()
    out = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = _coerce(v)
    return out


def _split_doc(text: str):
    if not text.startswith(_FENCE):
        return {}, text
    end = text.find("\n" + _FENCE, len(_FENCE))
    if end < 0:
        return {}, text
    fm = {}
    for line in text[len(_FENCE):end].strip().splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = _coerce(v)
    body_start = end + len("\n" + _FENCE)
    return fm, text[body_start:].lstrip("\n")


def _render(fm: dict, body: str) -> str:
    lines = [_FENCE]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append(_FENCE)
    return "\n".join(lines) + "\n\n" + body


def write_index(path: Path, frontmatter: dict, contexts: list) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    body_lines = ["# Session Summary", "", "(in progress)", "", _CONTEXT_HEADING, ""]
    for c in contexts:
        body_lines.append(f"- [{c['filename']}] — {c['summary']}")
    body_lines.append("")
    body_lines.append("---")
    session_prefix = str(frontmatter.get("session_id", ""))[:8]
    body_lines.append(_RESUME_HINT.format(session_prefix=session_prefix))
    body_lines.append("")
    p.write_text(_render(frontmatter, "\n".join(body_lines)))


def append_context_entry(path: Path, filename: str, summary: str) -> None:
    p = Path(path)
    fm, body = _split_doc(p.read_text())
    lines = body.splitlines()
    try:
        h = lines.index(_CONTEXT_HEADING)
    except ValueError:
        lines.extend([_CONTEXT_HEADING, ""])
        h = len(lines) - 2
    insert_at = h + 2
    while insert_at < len(lines) and lines[insert_at].startswith("- ["):
        insert_at += 1
    lines.insert(insert_at, f"- [{filename}] — {summary}")
    p.write_text(_render(fm, "\n".join(lines) + ("\n" if not body.endswith("\n") else "")))


def update_frontmatter(path: Path, **updates) -> None:
    p = Path(path)
    fm, body = _split_doc(p.read_text())
    fm.update(updates)
    p.write_text(_render(fm, body))
