import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from session_state import _TRANSCRIPT_WINDOW, _TRANSCRIPT_MAX_CHARS


def extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [c.get("text", "").strip() for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def parse_transcript(path: str) -> list[dict]:
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
                msg = entry.get("message")
                if not msg:
                    continue
                text = extract_text(msg.get("content", ""))
                if text:
                    messages.append({
                        "role": msg.get("role", ""),
                        "text": text,
                        "uuid": entry.get("uuid", ""),
                    })
    except (FileNotFoundError, OSError):
        pass
    return messages


def detect_domains_free_form(messages: list[dict]) -> list[str]:
    if not messages:
        return []
    text_parts = [m.get("text", "") for m in messages[-_TRANSCRIPT_WINDOW:]]
    transcript_sample = "\n".join(text_parts)[:_TRANSCRIPT_MAX_CHARS]
    prompt = (
        "Read the following conversation and return a JSON array of domains "
        "that were substantively worked on (e.g. kubernetes, finance, rust, pine-script).\n\n"
        f"Transcript:\n{transcript_sample}\n\n"
        "Output ONLY a JSON array. No other text."
    )
    env = {**os.environ, "CLAUDE_WRITING_CONTEXT": "1"}
    try:
        r = subprocess.run(
            ["claude", "-p", "--no-session-persistence", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        if r.returncode != 0:
            return []
        data = json.loads(r.stdout)
        result_text = data.get("result", "").strip()
        detected = json.loads(result_text)
        if isinstance(detected, list):
            return [str(d).strip() for d in detected if str(d).strip()]
    except Exception:
        pass
    return []
