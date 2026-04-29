"""SessionStart source dispatch with ≤8KB budget per injection."""
import datetime
import json
import os
import re
from pathlib import Path

import project_root
import retention

INJECTION_BUDGET = 8_000
MAINTENANCE_INTERVAL_SECONDS = 24 * 3600
ARCHIVE_AGE_DAYS = 30
INSIGHT_CAP = 200
INSIGHT_MOVE = 50

_SAFE_SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _is_safe_session_id(s: str) -> bool:
    return bool(s) and bool(_SAFE_SESSION_ID_RE.match(s))


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


def _log_maintenance(sessions_dir: Path, action: str, detail: dict) -> None:
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        log_path = sessions_dir / ".maintenance_log.jsonl"
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": action,
            **detail,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _maybe_run_maintenance(cwd: Path) -> dict:
    """Run 24h-throttled archive + INSIGHT rotation. Silent on failure."""
    result = {"archived_count": 0, "insight_rotated": False}
    sessions_dir = cwd / ".claude" / "sessions"
    state_path = sessions_dir / ".maintenance_state.json"
    now = datetime.datetime.now(datetime.timezone.utc)

    try:
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            last = state.get("last_archive_at")
            if last:
                try:
                    last_dt = datetime.datetime.fromisoformat(last)
                    if (now - last_dt).total_seconds() < MAINTENANCE_INTERVAL_SECONDS:
                        return result
                except Exception:
                    pass
    except Exception:
        pass

    try:
        archived = retention.archive_old_sessions(sessions_dir, ARCHIVE_AGE_DAYS)
        result["archived_count"] = len(archived)
        if archived:
            _log_maintenance(sessions_dir, "archive", {"sessions": archived})
    except Exception as e:
        _log_maintenance(sessions_dir, "archive_error", {"error": str(e)})

    try:
        insight_path = cwd / ".claude" / "INSIGHT.md"
        rotated = retention.rotate_insight(insight_path, INSIGHT_CAP, INSIGHT_MOVE)
        if rotated is not None:
            result["insight_rotated"] = True
            _log_maintenance(sessions_dir, "rotate_insight", {"archive": str(rotated)})
    except Exception as e:
        _log_maintenance(sessions_dir, "rotate_insight_error", {"error": str(e)})

    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"last_archive_at": now.isoformat()}),
            encoding="utf-8",
        )
    except Exception:
        pass

    return result


def _detect_pollution_warning(cwd: Path) -> "str | None":
    """One-time per-repo warning when subpackage .claude/ directories exist."""
    try:
        polluted = project_root.detect_subpackage_pollution(cwd)
    except Exception:
        return None
    if not polluted:
        return None
    sessions_dir = cwd / ".claude" / "sessions"
    flag = sessions_dir / ".pollution_warned"
    if flag.exists():
        return None
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        flag.write_text(
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            encoding="utf-8",
        )
    except Exception:
        pass
    rels = []
    for p in polluted[:3]:
        try:
            rels.append(str(p.relative_to(cwd)))
        except ValueError:
            rels.append(str(p))
    suffix = "" if len(polluted) <= 3 else f" (+{len(polluted) - 3} more)"
    return (
        "subpackage .claude/ found at "
        + ", ".join(rels)
        + suffix
        + " — should be at repo root"
    )


def handle(payload: dict) -> None:
    source = payload.get("source", "startup")
    session_id = payload.get("session_id", "")
    if session_id and not _is_safe_session_id(session_id):
        return
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

    maint = _maybe_run_maintenance(cwd)
    pollution_msg = _detect_pollution_warning(cwd)

    parts = []
    if maint.get("archived_count"):
        parts.append(f"archived {maint['archived_count']} session(s)")
    if maint.get("insight_rotated"):
        parts.append("rotated INSIGHT.md")
    if pollution_msg:
        parts.append(pollution_msg)
    system_message = "session-memory: " + "; ".join(parts) if parts else ""

    body = _load_insight(cwd, INJECTION_BUDGET)
    if body:
        _emit(
            f"<codebase-insights>\n{body}\n</codebase-insights>",
            system_message=system_message,
        )
    elif system_message:
        _emit("", system_message=system_message)
