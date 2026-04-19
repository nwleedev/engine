import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import find_project_root, resolve_cwd, get_harness_dir
from check_violations import parse_violation_line


def build_violation_summary(log_path: Path) -> str:
    if not log_path.exists():
        return ""

    cutoff = datetime.now() - timedelta(days=30)
    rule_counts: dict[str, int] = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        v = parse_violation_line(line)
        if not v:
            continue
        try:
            date = datetime.strptime(v["date"], "%Y-%m-%d")
            if date < cutoff:
                continue
        except ValueError:
            continue
        key = f"{v['domain']}::{v['rule']}"
        rule_counts[key] = rule_counts.get(key, 0) + 1

    repeated = {k: c for k, c in rule_counts.items() if c >= 2}
    if not repeated:
        return ""

    lines = ["## Harness Warnings", "Repeated violations from previous sessions:"]
    for key, count in sorted(repeated.items(), key=lambda x: -x[1]):
        domain, rule = key.split("::", 1)
        lines.append(f"- [{domain}] {rule} ({count} times)")
    lines.append("→ Pay special attention to these patterns in today's work.")
    return "\n".join(lines)


def main() -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT") == "1":
        return
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    cwd = resolve_cwd(payload)
    if not cwd:
        return

    project_root = find_project_root(cwd)
    harness_dir = get_harness_dir(project_root)
    log_path = harness_dir / "violations.log"

    summary = build_violation_summary(log_path)
    if not summary:
        return

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
