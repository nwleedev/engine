import json
import os
import subprocess
from pathlib import Path


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


def get_user_domains() -> list[str]:
    raw = os.environ.get("DOMAIN_PROFESSOR_DOMAINS", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(d).strip() for d in parsed if str(d).strip()]
    except json.JSONDecodeError:
        pass
    return [d.strip() for d in raw.split(",") if d.strip()]


def detect_domains_with_llm(messages: list[dict], domains: list[str]) -> list[str]:
    if not domains or not messages:
        return []
    text_parts = [m.get("text", "") for m in messages[-20:]]
    transcript_sample = "\n".join(text_parts)[:4000]
    prompt = (
        "다음 대화 기록을 읽고, 아래 도메인 목록 중 이 대화에서 실질적으로 다루어진 도메인만 골라서 "
        "JSON 배열로 반환하세요.\n\n"
        f"도메인 목록: {json.dumps(domains, ensure_ascii=False)}\n\n"
        f"대화 기록:\n{transcript_sample}\n\n"
        "실질적으로 다루어진 도메인만 포함하세요. 단순히 언급만 된 것은 제외하세요.\n"
        "응답 형식: [\"domain1\", \"domain2\"] 형태의 JSON 배열만 출력하세요. 다른 텍스트는 포함하지 마세요."
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
            return [d for d in detected if d in domains]
    except Exception:
        pass
    return []


def detect_domains_from_transcript(transcript_path: str) -> list[str]:
    domains = get_user_domains()
    if not domains:
        return []
    messages = parse_transcript(transcript_path)
    return detect_domains_with_llm(messages, domains)
