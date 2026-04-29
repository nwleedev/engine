"""SessionStart source dispatch with ≤8KB budget per injection."""
import json
import os
from pathlib import Path

import project_root

INJECTION_BUDGET = 8_000


def _load_insight(cwd: Path, max_chars: int) -> str:
    p = Path(cwd) / ".claude" / "INSIGHT.md"
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8")
        entries = [e.strip() for e in text.split("\n---\n") if e.strip()]
        out = []
        total = 0
        for e in reversed(entries):
            remaining = max_chars - total
            if remaining <= 0:
                break
            if len(e) <= remaining:
                out.append(e)
                total += len(e)
            else:
                # truncate last entry to fit budget
                out.append(e[:remaining])
                total += remaining
                break
        out.reverse()
        return "\n\n---\n\n".join(out)
    except Exception:
        return ""


def _load_session_contexts(session_dir: Path, max_chars: int) -> str:
    contexts = session_dir / "contexts"
    if not contexts.exists():
        return ""
    files = sorted(contexts.glob("CONTEXT-*.md"), reverse=True)[:3]
    out = []
    total = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8").strip()
            remaining = max_chars - total
            if remaining <= 0:
                break
            if len(text) <= remaining:
                out.append(text)
                total += len(text)
            else:
                out.append(text[:remaining])
                total += remaining
                break
        except Exception:
            continue
    out.reverse()
    return "\n\n---\n\n".join(out)


def _load_session_index(session_dir: Path, max_chars: int) -> str:
    p = session_dir / "INDEX.md"
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8")
        return text[:max_chars]
    except Exception:
        return ""


def _emit(content: str, system_message: str = "") -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": content,
        }
    }
    if system_message:
        output["systemMessage"] = system_message
    print(json.dumps(output, ensure_ascii=False))


def handle(payload: dict) -> None:
    source = payload.get("source", "startup")
    session_id = payload.get("session_id", "")
    cwd_raw = (payload.get("cwd")
               or os.environ.get("CLAUDE_PROJECT_DIR", "")
               or os.environ.get("PWD", ""))
    if not cwd_raw:
        return
    cwd = Path(project_root.find_project_root(cwd_raw))
    session_dir = cwd / ".claude" / "sessions" / session_id

    if source == "clear":
        return

    if source == "compact":
        body = _load_session_contexts(session_dir, INJECTION_BUDGET)
        if body:
            _emit(f"<session-context>\n{body}\n</session-context>",
                  system_message="session-memory: 압축 후 컨텍스트 복원")
        return

    if source == "resume":
        body = _load_session_index(session_dir, INJECTION_BUDGET)
        if body:
            _emit(f"<session-resume>\n{body}\n</session-resume>")
        return

    body = _load_insight(cwd, INJECTION_BUDGET)
    if body:
        _emit(f"<codebase-insights>\n{body}\n</codebase-insights>")
