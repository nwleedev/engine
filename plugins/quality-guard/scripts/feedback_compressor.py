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
    rules_section = existing_rules.strip() if existing_rules.strip() else "(none)"
    return f"""\
The following are bias utterance quotes observed in a Claude Code session:

{quoted}

Existing rules:
{rules_section}

Merge the quotes above with the existing rules into at most 10 behavioral rules.
- Merge similar items into one rule
- Include the observation date in [YYYY-MM-DD] format
- Reply with JSON only: {{"rules": ["rule1 [date]", ...]}}
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
            if isinstance(rules, list) and all(isinstance(r, str) for r in rules):
                return rules
            pos = start + 1
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
        if not rules:
            return
        write_rules_md(cwd, rules, source_count=len(entries))
        reset_raw_md(cwd)
    except Exception:
        return
