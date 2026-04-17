#!/usr/bin/env python3
"""SessionStart hook: injects recent session context as additionalContext."""
import json, os, subprocess, sys
from pathlib import Path

import handwrite_context as hw


def resolve_cwd(payload):
    """Resolve project directory: payload.cwd → $CLAUDE_PROJECT_DIR → $PWD."""
    return (payload.get("cwd", "")
            or os.environ.get("CLAUDE_PROJECT_DIR", "")
            or os.environ.get("PWD", ""))


def load_recent_sessions(sessions_dir, current_session_id, max_sessions=3):
    """Load up to max_sessions recent sessions, excluding current session."""
    sessions = []
    sessions_dir = Path(sessions_dir)
    if not sessions_dir.exists():
        return []
    for session_path in sessions_dir.iterdir():
        if not session_path.is_dir():
            continue
        if session_path.name == current_session_id:
            continue
        index_path = session_path / "INDEX.md"
        if not index_path.exists():
            continue
        try:
            content = index_path.read_text(encoding="utf-8")
            fm, body = hw.parse_frontmatter(content)
            last_updated = fm.get("last_updated", "")
            sessions.append((last_updated, session_path, fm, body, content))
        except Exception:
            continue
    sessions.sort(key=lambda x: x[0], reverse=True)
    return sessions[:max_sessions]


def build_context_text(sessions):
    """Build additionalContext string from session list."""
    if not sessions:
        return ""
    parts = ["## 이전 작업 컨텍스트", ""]
    for i, (_, session_path, fm, body, raw_content) in enumerate(sessions):
        session_id = fm.get("session_id", session_path.name)
        short_id = session_id[:8] + "..." if len(session_id) > 8 else session_id
        if i == 0:
            parts.append(f"### 최근 세션 ({short_id})")
            parts.append("")
            parts.append(raw_content.strip())
            contexts_dir = session_path / "contexts"
            if contexts_dir.exists():
                ctx_files = sorted(contexts_dir.glob("CONTEXT-*.md"), reverse=True)[:3]
                for ctx in reversed(ctx_files):
                    try:
                        parts += ["", "---", ""]
                        parts.append(ctx.read_text(encoding="utf-8").strip())
                    except Exception:
                        continue
        else:
            parts.append(f"### 이전 세션 ({short_id})")
            parts.append("")
            parts.append(raw_content.strip())
        parts.append("")
    return "\n".join(parts)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = payload.get("session_id", "")
    cwd = resolve_cwd(payload)
    if not cwd:
        sys.exit(0)
    cwd = hw.find_project_root(cwd)

    sessions_dir = Path(cwd) / ".claude" / "sessions"
    sessions = load_recent_sessions(sessions_dir, current_session_id=session_id)
    if not sessions:
        sys.exit(0)

    context_text = build_context_text(sessions)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context_text,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
