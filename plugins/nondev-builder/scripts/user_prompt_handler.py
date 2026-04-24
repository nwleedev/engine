import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nondev_io import read_index, read_rubric


def match_domain(prompt: str, domains: list[dict]) -> dict | None:
    prompt_lower = prompt.lower()
    for domain in domains:
        keywords = domain.get("keywords", {})
        for kw in keywords.get("ko", []):
            if kw.lower() in prompt_lower:
                return domain
        for kw in keywords.get("en", []):
            if kw.lower() in prompt_lower:
                return domain
    return None


def build_rubric_context(rubrics: list[tuple[str, str]]) -> str:
    if not rubrics:
        return ""
    parts = [
        "Apply the following nondev quality rubrics when generating your response.",
        "If your planned response would trigger any violation criteria, revise before outputting.",
        "",
    ]
    for task_name, rubric_content in rubrics:
        parts.append(f"### {task_name}\n{rubric_content}")
    return "\n".join(parts)


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    prompt = payload.get("prompt", "")
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
    rubric_context = build_rubric_context(rubrics)

    command_hint = ""
    if prompt:
        matched = match_domain(prompt, domains)
        if matched:
            task_name = matched.get("task_name", "")
            command = matched.get("command", f"/{task_name}")
            command_hint = (
                f"[{task_name} domain detected] "
                f"Run {command} [goal] for parallel research + independent evaluation."
            )

    combined = "\n\n".join(filter(None, [rubric_context, command_hint]))
    if not combined:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": combined,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
        main_with_payload(payload)
    except Exception:
        pass


if __name__ == "__main__":
    main()
