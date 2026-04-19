#!/usr/bin/env python3
"""Stop hook: generates narration context after each Claude turn."""
import json, os, re, subprocess, sys
from datetime import datetime
from pathlib import Path

CHAR_LIMIT = 80_000


def _debug(msg):
    """Write a debug message to stderr when SESSION_MEMORY_DEBUG is set."""
    if os.environ.get("SESSION_MEMORY_DEBUG"):
        print(f"[session-memory] {msg}", file=sys.stderr)


SECTION_HEADERS = {
    "ko": {
        "what_why": "## 무엇을 왜",
        "decisions": "## 주요 결정",
        "incomplete": "## 미완료",
        "next_instructions": "## 다음 세션 지침",
    },
    "en": {
        "what_why": "## What & Why",
        "decisions": "## Key Decisions",
        "incomplete": "## Incomplete",
        "next_instructions": "## Instructions for Next Session",
    },
}


def extract_text(content):
    """Extract plain text from message content (str or list)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [c.get("text", "").strip() for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def parse_transcript(path):
    """Parse transcript JSONL. Returns (cwd, messages).
    messages: list of {uuid, role, text}
    """
    cwd = ""
    messages = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not cwd and entry.get("cwd"):
                    cwd = entry["cwd"]
                msg = entry.get("message", {})
                role = msg.get("role")
                if role in ("user", "assistant"):
                    text = extract_text(msg.get("content", ""))
                    if text:
                        messages.append({
                            "uuid": entry.get("uuid", ""),
                            "role": role,
                            "text": text,
                        })
    except Exception:
        pass
    return cwd, messages


def extract_delta(messages, last_processed_uuid):
    """Return messages after last_processed_uuid. If None, return all."""
    if not last_processed_uuid:
        return messages
    found = False
    delta = []
    for msg in messages:
        if found:
            delta.append(msg)
        if msg.get("uuid") == last_processed_uuid:
            found = True
    if not found:
        return messages  # transcript rotated; use all messages as fallback
    return delta


def format_messages(messages):
    """Format messages list as plain text for prompt."""
    return "\n".join(f"[{m['role']}] {m['text']}" for m in messages)


def truncate_messages(messages, max_chars=CHAR_LIMIT):
    """Keep most-recent messages within max_chars. Returns (text, was_truncated)."""
    full_text = format_messages(messages)
    if len(full_text) <= max_chars:
        return full_text, False
    kept = []
    total = 0
    for msg in reversed(messages):
        line = f"[{msg['role']}] {msg['text']}\n"
        if total + len(line) > max_chars:
            break
        kept.insert(0, msg)
        total += len(line)
    return format_messages(kept), True


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown string. Returns (dict, body_str)."""
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        return {}, content
    fm = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, content[match.end():]


def read_index(session_dir):
    """Read INDEX.md frontmatter. Returns dict or None if missing."""
    index_path = Path(session_dir) / "INDEX.md"
    if not index_path.exists():
        return None
    fm, _ = parse_frontmatter(index_path.read_text(encoding="utf-8"))
    return fm if fm else None


def create_index(session_dir, session_id, cwd):
    """Create session directory and empty INDEX.md. Returns initial frontmatter dict."""
    session_dir = Path(session_dir)
    (session_dir / "contexts").mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    fm = {
        "session_id": session_id,
        "cwd": cwd,
        "started": now,
        "last_updated": now,
        "last_processed_uuid": "",
        "context_head": "",
        "last_context_written_at": "",
    }
    body = f"\n# 세션 요약\n\n(진행 중)\n\n## 컨텍스트 목록\n\n---\n이 세션 재개: `claude -r {session_id}`\n"
    _write_index_file(session_dir, fm, body)
    return fm


def _write_index_file(session_dir, fm, body):
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines += ["---", ""]
    content = "\n".join(lines) + body
    (Path(session_dir) / "INDEX.md").write_text(content, encoding="utf-8")


def update_index(session_dir, fm, last_uuid, new_head, context_num, title, one_liner):
    """Update INDEX.md with new context entry and updated frontmatter."""
    session_dir = Path(session_dir)
    index_path = session_dir / "INDEX.md"
    _, body = parse_frontmatter(index_path.read_text(encoding="utf-8"))

    fm["last_processed_uuid"] = last_uuid
    fm["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    fm["last_context_written_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    if new_head:
        fm["context_head"] = new_head

    entry = f"- [{context_num:04d}] {title} — {one_liner}\n"
    if "\n---\n" in body:
        body = body.replace("\n---\n", f"\n{entry}---\n", 1)
    else:
        body += entry

    _write_index_file(session_dir, fm, body)


def get_next_context_number(session_dir):
    """Return next sequential number for CONTEXT file."""
    contexts_dir = Path(session_dir) / "contexts"
    existing = list(contexts_dir.glob("CONTEXT-*.md"))
    return len(existing) + 1


def write_context_file(session_dir, num, title, narration, commits, session_id):
    """Write CONTEXT-####-<title>.md to session contexts directory."""
    contexts_dir = Path(session_dir) / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    filename = f"CONTEXT-{num:04d}-{title}.md"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# CONTEXT-{num:04d}: {title}",
        "",
        f"**날짜**: {now}  ",
        f"**세션**: {session_id}",
        "",
        "## 작업 나레이션",
        "",
        narration,
        "",
    ]
    if commits:
        lines += ["## 관련 커밋", ""]
        for c in commits:
            lines.append(f"- `{c}`")
        lines.append("")
    lines += ["---", "", f"이 세션 재개: `claude -r {session_id}`", ""]

    (contexts_dir / filename).write_text("\n".join(lines), encoding="utf-8")


def find_project_root(cwd):
    """Find project root: git root → .claude parent walk-up → cwd.

    In a monorepo where claude runs from a subdirectory (e.g. web/), this
    returns the repo root so all sessions share one .claude/sessions/ tree.
    """
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    # Walk up looking for an existing .claude/ directory
    path = Path(cwd)
    for candidate in [path] + list(path.parents):
        if (candidate / ".claude").is_dir():
            return str(candidate)
    return cwd


def get_git_head(cwd):
    """Return current HEAD hash, or empty string if not a git repo."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def get_git_commits(cwd, context_head, session_started):
    """Return list of commit oneline strings since last context or session start."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            return []
        if context_head:
            cmd = ["git", "-C", cwd, "log", f"{context_head}..HEAD", "--oneline"]
        elif session_started:
            cmd = ["git", "-C", cwd, "log", f"--since={session_started}", "--oneline"]
        else:
            return []
        r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r2.returncode != 0:
            return []
        lines = [l.strip() for l in r2.stdout.strip().split("\n") if l.strip()]
        return lines
    except Exception:
        return []


_NARRATION_PROMPT = """\
You are reviewing a Claude Code work turn. Respond ONLY with valid JSON matching this schema exactly. No other text.
Write title in English. Write what_why, decisions, incomplete, and next_instructions in {language}.

{{
  "title": "2-3 word english slug, hyphens, lowercase. e.g. jwt-token-setup",
  "what_why": "Plain prose. What was done and WHY. No filenames or function names. Distinguish completed vs incomplete work. Scale length to complexity (simple: 3-5 sentences, moderate: 8-12, complex: 15-20).",
  "decisions": ["Key decision with rationale. Include rejected alternatives and reasons."],
  "incomplete": ["Unfinished item"],
  "next_instructions": "Imperative directives for the next session. e.g. When working on X, verify Y first."
}}

{truncation_note}Conversation:
{delta_text}
"""


_INSIGHT_RE = re.compile(
    r'`★ Insight[ ─]+`\n(.*?)\n`[─]+`',
    re.DOTALL,
)


def extract_insights(messages):
    """Return ★ Insight block contents from assistant messages in delta."""
    out = []
    for msg in messages:
        if msg.get("role") == "assistant":
            for m in _INSIGHT_RE.finditer(msg.get("text", "")):
                content = m.group(1).strip()
                if content:
                    out.append(content)
    return out


def append_insights_to_project(cwd, insights, session_id):
    """Append new insights to {cwd}/.claude/INSIGHT.md, skipping duplicates."""
    if not insights:
        return
    try:
        path = Path(cwd) / ".claude" / "INSIGHT.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        sid_short = session_id[:8]
        new_lines = []
        for insight in insights:
            if insight not in existing:
                new_lines.append(
                    f"\n---\n**{now}** · `{sid_short}`\n\n{insight}\n"
                )
        if new_lines:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write("".join(new_lines))
    except Exception as e:
        _debug(f"append_insights_to_project failed: {e}")


def build_prompt(delta_text: str, was_truncated: bool, language: str = "en") -> str:
    """Build the prompt string for claude -p."""
    note = "Note: earlier messages omitted due to length.\n\n" if was_truncated else ""
    return _NARRATION_PROMPT.format(
        language=language,
        truncation_note=note,
        delta_text=delta_text,
    )


def call_claude_narration(delta_text: str, was_truncated: bool, language: str = "en"):
    """Call claude -p to generate structured narration. Returns dict or None."""
    prompt = build_prompt(delta_text, was_truncated, language)
    env = {**os.environ, "CLAUDE_WRITING_CONTEXT": "1"}
    try:
        r = subprocess.run(
            ["claude", "-p", "--no-session-persistence", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if r.returncode != 0:
            _debug(f"claude -p failed (rc={r.returncode}): {r.stderr[:300]}")
            return None
        outer = json.loads(r.stdout)
        inner_text = outer.get("result", "")
        stripped = inner_text.strip()
        # Iterate every { position with raw_decode — handles:
        # Mode 1: ★ Insight preamble before JSON (json_start > 0)
        # Mode 2: trailing content after JSON (raw_decode stops at end of object)
        # Mode 3: no valid JSON at all (returns None)
        pos = 0
        while True:
            json_start = stripped.find('{', pos)
            if json_start < 0:
                break
            try:
                obj, _ = json.JSONDecoder().raw_decode(stripped[json_start:])
                return obj
            except json.JSONDecodeError:
                pos = json_start + 1
        _debug(f"Mode 3: no JSON in claude -p response: {stripped[:300]}")
        return None  # Mode 3: no valid JSON — do not store garbage
    except Exception as e:
        _debug(f"exception in call_claude_narration: {e}")
        return None


def main():
    # Guard: prevent recursive calls from claude -p subprocess
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

    cwd, messages = parse_transcript(transcript_path)
    if not cwd or not messages:
        sys.exit(0)
    cwd = find_project_root(cwd)

    session_dir = Path(cwd) / ".claude" / "sessions" / session_id
    index_data = read_index(session_dir) or create_index(session_dir, session_id, cwd)

    delta = extract_delta(messages, index_data.get("last_processed_uuid") or "")
    if not delta:
        if messages:
            index_data["last_processed_uuid"] = messages[-1].get("uuid", "")
            _write_index_file(session_dir, index_data,
                              parse_frontmatter((session_dir / "INDEX.md").read_text())[1])
        sys.exit(0)

    # Extract insights before narration so the variable exists for later use
    insights = extract_insights(delta)

    delta_text, was_truncated = truncate_messages(delta)
    result = call_claude_narration(delta_text, was_truncated)
    if not result:
        sys.exit(0)

    commits = get_git_commits(cwd, index_data.get("context_head"), index_data.get("started"))

    title = result.get("title") or "checkpoint-" + datetime.utcnow().strftime("%m%d-%H%M")
    narration = result.get("narration", "")
    one_liner = narration.split("。")[0].split(".")[0][:80] if narration else title

    num = get_next_context_number(session_dir)
    write_context_file(session_dir, num, title, narration, commits, session_id)

    new_head = get_git_head(cwd)
    last_uuid = delta[-1].get("uuid", "")
    update_index(session_dir, index_data, last_uuid, new_head, num, title, one_liner)

    if insights:
        append_insights_to_project(cwd, insights, session_id)


if __name__ == "__main__":
    main()
