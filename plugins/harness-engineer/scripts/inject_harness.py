_CORE_RULES_HEADERS = ["## 핵심 규칙", "## Core Rules"]


def extract_core_rules(content: str) -> str:
    lines = content.splitlines()
    in_section = False
    result = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(h) for h in _CORE_RULES_HEADERS):
            in_section = True
            result.append(line)
            continue
        if in_section:
            if stripped.startswith("## "):
                break
            result.append(line)
    return "\n".join(result[:15]).strip()


def build_user_prompt_context(matched_files: list[dict]) -> str:
    if not matched_files:
        return ""
    return "\n\n---\n\n".join(f["content"] for f in matched_files)


def build_pre_tool_context(harness_file: dict) -> str:
    domain = harness_file["domain"]
    rules = extract_core_rules(harness_file["content"])
    if not rules:
        return ""
    return f"[harness 체크] {domain}\n{rules}"
