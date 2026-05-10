"""Single orchestrator for narration: parse -> gate -> narrate -> write -> log."""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import index_io
import lang_detect
import log as lg
import narration_state
import one_liner
import policy
import project_root

NARRATION_TIMEOUT = 90
HAIKU_MODEL = "claude-haiku-4-5-20251001"

_SAFE_SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _is_safe_session_id(s: str) -> bool:
    return bool(s) and bool(_SAFE_SESSION_ID_RE.match(s))

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

NARRATION_PROMPT = """\
You are reviewing a Claude Code work turn. Respond ONLY with valid JSON matching this schema. No other text.
Title in English. Body fields in {language}.

{{
  "title": "2-3 word english slug, hyphens, lowercase",
  "what_why": "Plain prose. What was done and WHY.",
  "decisions": ["Key decision with rationale"],
  "incomplete": ["Unfinished item"],
  "next_instructions": "Imperative directives for the next session."
}}

{truncation_note}Conversation:
{delta_text}
"""


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [c.get("text", "").strip() for c in content if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def _parse_transcript(path: str):
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
                    text = _extract_text(msg.get("content", ""))
                    if text:
                        messages.append({"uuid": entry.get("uuid", ""), "role": role, "text": text})
    except Exception:
        pass
    return cwd, messages


def _extract_delta(messages, last_uuid):
    if not last_uuid:
        return messages
    found = False
    delta = []
    for m in messages:
        if found:
            delta.append(m)
        if m.get("uuid") == last_uuid:
            found = True
    return delta if found else messages


def _truncate_for_input(messages, cap_chars):
    text = policy.format_messages(messages)
    if len(text) <= cap_chars:
        return text, False
    kept = []
    total = 0
    for m in reversed(messages):
        line = f"[{m['role']}] {m['text']}\n"
        if total + len(line) > cap_chars:
            break
        kept.insert(0, m)
        total += len(line)
    return policy.format_messages(kept), True


def _call_claude(prompt: str, use_fallback: bool, log_path: Path):
    cmd = ["claude", "-p", "--no-session-persistence", "--output-format", "json"]
    if not use_fallback:
        cmd += ["--model", HAIKU_MODEL]
    lg.append(log_path, {"event": "narration_call", "model": "default" if use_fallback else "haiku-4-5"})
    env = {**os.environ, "CLAUDE_WRITING_CONTEXT": "1"}
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=NARRATION_TIMEOUT, env=env)
        if r.returncode != 0:
            lg.append(log_path, {"event": "narration_subprocess_fail", "rc": r.returncode, "stderr": (r.stderr or "")[:200]})
            return None
        outer = json.loads(r.stdout)
        stripped = (outer.get("result", "") or "").strip()
        pos = 0
        while True:
            start = stripped.find("{", pos)
            if start < 0:
                break
            try:
                obj, _ = json.JSONDecoder().raw_decode(stripped[start:])
                return obj
            except json.JSONDecodeError:
                pos = start + 1
        lg.append(log_path, {"event": "narration_parse_fail", "preview": stripped[:200]})
        return None
    except Exception as e:
        lg.append(log_path, {"event": "narration_exception", "error": str(e)[:200]})
        return None


def _build_prompt(delta_text: str, truncated: bool, lang: str) -> str:
    note = "Note: earlier messages omitted due to length.\n\n" if truncated else ""
    return NARRATION_PROMPT.format(language=lang, truncation_note=note, delta_text=delta_text)


def _hourly_path(session_dir: Path, title: str) -> Path:
    prefix = "CONTEXT-" + datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y%m%d-%H00-")
    contexts = session_dir / "contexts"
    contexts.mkdir(parents=True, exist_ok=True)
    existing = sorted(contexts.glob(f"{prefix}*.md"))
    if existing:
        return existing[0]
    return contexts / f"{prefix}{title}.md"


def _write_context_file(session_dir: Path, title: str, lang: str, result: dict, session_id: str) -> str:
    path = _hourly_path(session_dir, title)
    headers = SECTION_HEADERS.get(lang, SECTION_HEADERS["en"])
    none_label = "없음" if lang == "ko" else "None"
    now = _utcnow_iso()
    sid_short = session_id[:8]

    lines = [f"<!-- session: {sid_short} · {now} -->", "",
             headers["what_why"], result.get("what_why", ""), "",
             headers["decisions"]]
    decisions = result.get("decisions") or [none_label]
    for d in decisions:
        lines.append(f"- {d}")
    lines += ["", headers["incomplete"]]
    incomplete = result.get("incomplete") or [none_label]
    for i in incomplete:
        lines.append(f"- {i}")
    lines += ["", headers["next_instructions"], result.get("next_instructions", ""), "", "---", ""]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path.name


def _git_head(cwd: str) -> str:
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return ""
        out = (r.stdout or "").strip()
        # Only accept hex sha-like output
        if re.fullmatch(r"[0-9a-f]{7,64}", out):
            return out
        return ""
    except Exception:
        return ""


def _resolve_root(cwd_raw: str) -> str:
    """Resolve project root robustly: validate git toplevel is a real directory."""
    try:
        candidate = project_root.find_project_root(cwd_raw)
        if candidate and Path(candidate).is_dir():
            return candidate
    except Exception:
        pass
    return cwd_raw


def run(event: str, payload: dict) -> None:
    """Orchestrator entry point."""
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        return

    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")
    if not session_id:
        return
    if not _is_safe_session_id(session_id):
        return

    cwd_raw, messages = _parse_transcript(transcript_path) if transcript_path else ("", [])
    if not cwd_raw:
        cwd_raw = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "") or os.environ.get("PWD", "")
    if not cwd_raw:
        return

    cwd = _resolve_root(cwd_raw)
    session_dir = Path(cwd) / ".claude" / "sessions" / session_id
    # Only enforce canonical-root check when git actually reports a real directory.
    try:
        git_top = project_root._git_toplevel(str(cwd_raw))
    except Exception:
        git_top = ""
    if git_top and Path(git_top).is_dir():
        try:
            project_root.assert_root_is_canonical(Path(cwd), Path(cwd_raw))
        except RuntimeError:
            return

    log_path = session_dir / "log.jsonl"
    index_data = index_io.read_index(session_dir)
    if not index_data:
        first_uuid = messages[0]["uuid"] if messages else ""
        index_data = index_io.create_index(session_dir, session_id, cwd, started_uuid=first_uuid)

    if messages and index_io.detect_rotation(session_dir, messages[0]["uuid"]):
        lg.append(log_path, {"event": "rotation_detected",
                              "old_started_uuid": index_data.get("started_uuid", ""),
                              "new_started_uuid": messages[0]["uuid"]})
        index_io.archive_on_rotation(session_dir)
        index_data = index_io.create_index(session_dir, session_id, cwd, started_uuid=messages[0]["uuid"])

    delta = _extract_delta(messages, index_data.get("last_processed_uuid", ""))
    if not policy.should_narrate(event, delta, index_data):
        lg.append(log_path, {"event": event, "decision": "skip",
                              "delta_chars": len(policy.format_messages(delta)) if delta else 0})
        return

    delta_text, truncated = _truncate_for_input(delta, policy.NARRATION_HARD_CAP)
    lang = lang_detect.detect(cwd)
    prompt = _build_prompt(delta_text, truncated, lang)

    use_fallback = narration_state.should_use_fallback(session_dir)
    result = _call_claude(prompt, use_fallback, log_path)

    if not result:
        narration_state.increment_failures(session_dir)
        lg.append(log_path, {"event": event, "decision": "narrate_failed"})
        return

    narration_state.reset_failures(session_dir)
    title = result.get("title") or "checkpoint-" + datetime.now(timezone.utc).replace(tzinfo=None).strftime("%m%d-%H%M")
    one = one_liner.extract(result.get("what_why", "") or title)
    filename = _write_context_file(session_dir, title, lang, result, session_id)
    last_uuid = delta[-1]["uuid"] if delta else ""
    index_io.update_entry(session_dir, filename, one, last_uuid=last_uuid, new_head=_git_head(cwd))
    lg.append(log_path, {"event": event, "decision": "narrate", "filename": filename,
                          "delta_chars": len(delta_text)})
