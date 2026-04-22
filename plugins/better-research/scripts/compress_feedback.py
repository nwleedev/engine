import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from feedback_io import load_raw_since_checkpoint, load_feedback_rules, reset_raw_md


def build_compression_prompt(entries: list[str], existing_rules: str) -> str:
    quoted = "\n".join(f'- "{e}"' for e in entries)
    rules_section = existing_rules.strip() if existing_rules.strip() else "(없음)"
    return f"""\
다음은 Claude Code 세션에서 관찰된 편향 발화 인용문들입니다:

{quoted}

기존 규칙:
{rules_section}

위 인용문들과 기존 규칙을 통합하여 최대 10개의 행동 규칙을 작성하세요.
- 유사한 내용은 하나로 합칠 것
- 관찰 날짜를 [YYYY-MM-DD] 형식으로 포함할 것
- 반드시 JSON으로만 응답: {{"rules": ["규칙1 [날짜]", ...]}}
"""


def parse_rules_from_result(result_text: str) -> list[str] | None:
    """Extract {"rules": [...]} from result text (may have preamble)."""
    pos = 0
    while True:
        start = result_text.find("{", pos)
        if start < 0:
            return None
        try:
            obj, _ = json.JSONDecoder().raw_decode(result_text[start:])
            rules = obj.get("rules")
            if isinstance(rules, list):
                return rules
            return None
        except json.JSONDecodeError:
            pos = start + 1


def write_rules_md(cwd: str, rules: list[str], source_count: int) -> None:
    path = Path(cwd) / ".claude" / "feedback" / "rules.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"<!-- auto-generated | updated: {now} | source-entries: {source_count} -->", ""]
    for rule in rules:
        lines.append(f"- {rule}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_compression(cwd: str) -> None:
    entries = load_raw_since_checkpoint(cwd)
    if not entries:
        return
    existing_rules = load_feedback_rules(cwd)
    prompt = build_compression_prompt(entries, existing_rules)
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
            return
        outer = json.loads(r.stdout)
        result_text = outer.get("result", "")
        rules = parse_rules_from_result(result_text)
        if rules is None:
            return
        write_rules_md(cwd, rules, source_count=len(entries))
        reset_raw_md(cwd)
    except Exception:
        return
