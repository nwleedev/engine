#!/usr/bin/env python3
"""PreToolUse hook: detects auto-compact and time-based checkpoints, generates CONTEXT + injects additionalContext."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import handwrite_context as hw

CHECKPOINT_INTERVAL = 300  # 5 minutes


def read_tail_lines(path, n=100):
    """Read last n lines of file efficiently without loading entire file."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        buf_size = min(size, n * 300)
        f.seek(max(0, size - buf_size))
        raw = f.read()
    lines = raw.decode("utf-8", errors="ignore").splitlines()
    return lines[-n:]


def find_unhandled_compact(transcript_path, last_compact_handled):
    """
    Scan last 100 lines of transcript for unhandled compact_boundary.
    Returns compact entry dict if found and not yet handled, else None.
    """
    try:
        lines = read_tail_lines(transcript_path, n=100)
    except Exception:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "system" and entry.get("subtype") == "compact_boundary":
            uid = entry.get("uuid", "")
            if uid and uid != last_compact_handled:
                return entry
            return None  # already handled or no uuid
    return None


def should_checkpoint(index_data, delta_text):
    """Returns True if time (>=5min) or size (>=80k chars) threshold exceeded."""
    if len(delta_text) >= hw.CHAR_LIMIT:
        return True
    last_written = index_data.get("last_context_written_at", "")
    if not last_written:
        return False
    try:
        last_dt = datetime.fromisoformat(last_written)
        elapsed = (datetime.utcnow() - last_dt).total_seconds()
        return elapsed >= CHECKPOINT_INTERVAL
    except Exception:
        return False


def build_compact_context(session_dir, session_id):
    """Build additionalContext string from current session's recent CONTEXT files."""
    contexts_dir = Path(session_dir) / "contexts"
    if not contexts_dir.exists():
        return ""
    ctx_files = sorted(contexts_dir.glob("CONTEXT-*.md"), reverse=True)[:3]
    if not ctx_files:
        return ""
    short_id = session_id[:9] + "..." if len(session_id) > 9 else session_id
    parts = [
        "## 현재 세션 컨텍스트",
        "",
        f"컨텍스트 압축이 발생했습니다. 이 세션({short_id})의 주요 작업 내용입니다.",
        "",
    ]
    for ctx in reversed(ctx_files):
        try:
            parts += ["---", "", ctx.read_text(encoding="utf-8").strip(), ""]
        except Exception:
            continue
    parts.append(f"이 세션 재개: `claude -r {session_id}`")
    return "\n".join(parts)


def main():
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        sys.exit(0)

    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")
    if not transcript_path or not session_id:
        sys.exit(0)

    cwd, messages = hw.parse_transcript(transcript_path)
    if not cwd:
        sys.exit(0)
    cwd = hw.find_project_root(cwd)

    session_dir = Path(cwd) / ".claude" / "sessions" / session_id
    index_data = hw.read_index(session_dir) or hw.create_index(session_dir, session_id, cwd)

    # ── Stage 1: compact detection ──
    compact_entry = find_unhandled_compact(
        transcript_path, index_data.get("last_compact_handled", "")
    )
    if compact_entry:
        compact_uid = compact_entry.get("uuid", "")
        delta = hw.extract_delta(messages, index_data.get("last_processed_uuid") or "")
        if not delta:
            index_data["last_compact_handled"] = compact_uid
            hw._write_index_file(
                session_dir, index_data,
                hw.parse_frontmatter((session_dir / "INDEX.md").read_text())[1]
            )
            sys.exit(0)
        delta_text, was_truncated = hw.truncate_messages(delta)
        result = hw.call_claude_narration(delta_text, was_truncated)
        if not result:
            sys.exit(0)
        commits = hw.get_git_commits(cwd, index_data.get("context_head"), index_data.get("started"))
        title = result.get("title") or "checkpoint-" + datetime.utcnow().strftime("%m%d-%H%M")
        narration = result.get("narration", "")
        one_liner = narration.split("。")[0].split(".")[0][:80] if narration else title
        num = hw.get_next_context_number(session_dir)
        hw.write_context_file(session_dir, num, title, narration, commits, session_id)
        new_head = hw.get_git_head(cwd)
        last_uuid = delta[-1].get("uuid", "")
        index_data["last_compact_handled"] = compact_uid
        hw.update_index(session_dir, index_data, last_uuid, new_head, num, title, one_liner)
        context_text = build_compact_context(session_dir, session_id)
        if context_text:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": context_text,
                }
            }, ensure_ascii=False))
        sys.exit(0)

    # ── Stage 2: time/size checkpoint ──
    delta = hw.extract_delta(messages, index_data.get("last_processed_uuid") or "")
    if not delta:
        sys.exit(0)
    delta_text, was_truncated = hw.truncate_messages(delta)
    if not should_checkpoint(index_data, delta_text):
        sys.exit(0)
    # Race condition guard: re-read index to catch processes that read the same
    # stale timestamp. Reduces but does not eliminate duplicate writes — a full
    # fix would require file locking or atomic rename (out of scope here).
    fresh = hw.read_index(session_dir)
    if fresh and fresh.get("last_context_written_at") != index_data.get("last_context_written_at"):
        sys.exit(0)
    result = hw.call_claude_narration(delta_text, was_truncated)
    if not result:
        sys.exit(0)
    commits = hw.get_git_commits(cwd, index_data.get("context_head"), index_data.get("started"))
    title = result.get("title", "untitled")
    narration = result.get("narration", "")
    one_liner = narration.split("。")[0].split(".")[0][:80] if narration else title
    num = hw.get_next_context_number(session_dir)
    hw.write_context_file(session_dir, num, title, narration, commits, session_id)
    new_head = hw.get_git_head(cwd)
    last_uuid = delta[-1].get("uuid", "")
    hw.update_index(session_dir, index_data, last_uuid, new_head, num, title, one_liner)


if __name__ == "__main__":
    main()
