import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nondev_io import read_index, read_rubric


def build_evaluation_prompt(rubrics: list[tuple[str, str]]) -> str:
    if not rubrics:
        return ""
    parts = [
        "Please evaluate your most recent response against the following nondev quality rubrics.",
        "If any violation criteria are triggered, revise your response in this turn (1 revision only).",
        "",
    ]
    for task_name, rubric_content in rubrics:
        parts.append(f"### {task_name}\n{rubric_content}")
    return "\n".join(parts)


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd") or os.getcwd()
    index = read_index(cwd)
    if not index:
        return
    domains = index.get("domains", [])
    if not domains:
        return

    rubrics: list[tuple[str, str]] = []
    for domain in domains:
        task_name = domain.get("task_name", "")
        if not task_name:
            continue
        rubric = read_rubric(cwd, task_name)
        if rubric:
            rubrics.append((task_name, rubric))

    if not rubrics:
        return

    context = build_evaluation_prompt(rubrics)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
