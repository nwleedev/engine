import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def extract_claude_code_blocks(transcript_path: str) -> list[str]:
    blocks = []
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content", "")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = "\n".join(
                        c.get("text", "") for c in content
                        if isinstance(c, dict) and c.get("type") == "text"
                    )
                in_block = False
                current: list[str] = []
                for text_line in text.splitlines():
                    if text_line.strip().startswith("```"):
                        if in_block:
                            if current:
                                blocks.append("\n".join(current))
                            current = []
                            in_block = False
                        else:
                            in_block = True
                    elif in_block:
                        current.append(text_line)
    except (FileNotFoundError, OSError):
        pass
    return blocks


def parse_violation_line(line: str) -> dict | None:
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 5:
        return None
    try:
        count_str = parts[4].replace("회 반복", "").strip()
        count = int(count_str)
    except ValueError:
        return None
    return {
        "date": parts[0],
        "domain": parts[1],
        "rule": parts[2],
        "location": parts[3],
        "count": count,
    }


def append_violations(violations: list[dict], log_path: Path) -> None:
    if not violations:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    for v in violations:
        date = v.get("date", today)
        line = f"{date} | {v['domain']} | {v['rule']} | {v['location']} | {v['count']}회 반복"
        lines.append(line)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _read_violations(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    parsed = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        v = parse_violation_line(line)
        if v:
            parsed.append(v)
    return parsed


def detect_drift(log_path: Path, harness_dir: Path) -> list[str]:
    warnings = []
    violations = _read_violations(log_path)

    rule_counts: dict[str, int] = {}
    for v in violations:
        key = f"{v['domain']}::{v['rule']}"
        rule_counts[key] = rule_counts.get(key, 0) + 1
    for key, count in rule_counts.items():
        if count >= 3:
            domain, rule = key.split("::", 1)
            warnings.append(f"[{domain}] '{rule}' 위반 {count}회 반복 → /update-harness {domain} 권고")

    cutoff = datetime.now() - timedelta(days=30)
    for md_file in harness_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith("updated:"):
                    date_str = line.split(":", 1)[1].strip()
                    updated = datetime.strptime(date_str, "%Y-%m-%d")
                    if updated < cutoff:
                        warnings.append(
                            f"[{md_file.stem}] harness 파일 마지막 갱신 {date_str} → /update-harness {md_file.stem} 권고"
                        )
                    break
        except (OSError, ValueError):
            continue
    return warnings


def trim_old_violations(log_path: Path, days: int = 90) -> None:
    if not log_path.exists():
        return
    cutoff = datetime.now() - timedelta(days=days)
    kept = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        v = parse_violation_line(line)
        if not v:
            kept.append(line)
            continue
        try:
            if datetime.strptime(v["date"], "%Y-%m-%d") >= cutoff:
                kept.append(line)
        except ValueError:
            kept.append(line)
    log_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def check_violations_with_llm(
    code_blocks: list[str],
    harness_files: list[dict],
    transcript_path: str,
) -> list[dict]:
    if not code_blocks or not harness_files:
        return []
    harness_summary = "\n\n".join(
        f"[{f['domain']}]\n{f['content'][:1000]}" for f in harness_files
    )
    code_sample = "\n---\n".join(code_blocks[:5])[:3000]
    prompt = (
        "다음 harness 규칙과 코드를 비교해서 위반 사항을 JSON 배열로 반환하세요.\n\n"
        f"Harness 규칙:\n{harness_summary}\n\n"
        f"작성된 코드:\n{code_sample}\n\n"
        '응답 형식: [{"domain":"react-frontend","rule":"any 타입 사용","location":"파일명:줄번호","count":1}]\n'
        "위반이 없으면 [] 를 반환하세요. JSON만 출력하세요."
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
        violations = json.loads(result_text)
        if isinstance(violations, list):
            return violations
    except Exception:
        pass
    return []
