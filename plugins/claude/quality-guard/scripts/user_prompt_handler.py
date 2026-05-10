import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from debiasing import build_core_debiasing, assemble_context
from project_root import find_project_root
from ref_index_reader import read_index

_QUALITY_INSTRUCTION_TEMPLATE = """\
<quality-instruction>
Available external references are registered in .claude/refs/INDEX.md.
For this response:
1. Check if any registered ref is relevant to the task.
2. If relevant: use the Read tool to read the ref file before responding.
3. Prioritise the external reference over your training-data defaults.
4. If no ref is relevant: apply the cognitive debiasing protocol instead.

Registered refs:
{index_content}
</quality-instruction>"""


def build_quality_instruction(index_content: str) -> str:
    return _QUALITY_INSTRUCTION_TEMPLATE.format(index_content=index_content.strip())


def main_with_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        return
    prompt = payload.get("prompt", "")
    if not prompt:
        return
    cwd_raw = payload.get("cwd", "") or os.getcwd()
    cwd = find_project_root(cwd_raw)

    index_content = read_index(cwd)
    if index_content:
        context = build_quality_instruction(index_content)
    else:
        context = build_core_debiasing()

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
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
