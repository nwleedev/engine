"""Build compact SessionStart context from saved session memory."""
import re
from pathlib import Path


TRUNCATION_MARKER = "\n...[truncated for Codex context budget]"
PLACEHOLDER_FILE_VALUES = {"", "없음", "none", "None", "n/a", "N/A", "저장된 파일 근거 없음"}
MINIMAL_PROMPT = "<codex-session-memory>\n</codex-session-memory>"
MIN_STRUCTURED_PROMPT_BUDGET = len(
    "\n".join([
        "<codex-session-memory>",
        "current_goal:",
        "last_known_state:",
        "files_and_branches:",
        "next_action:",
        "</codex-session-memory>",
    ])
)
MIN_SMALL_BUDGET_WITH_TAGS = 120
STRUCTURED_PROMPT_EMPTY = "\n".join([
    "<codex-session-memory>",
    "current_goal: 이어진 Codex 작업 맥락을 복원한다.",
    "last_known_state:",
    "",
    "files_and_branches:",
    "",
    "next_action:",
    "",
    "</codex-session-memory>",
])


def _context_names_from_index(index_text: str) -> list[str]:
    names = []
    in_context_list = False
    for line in index_text.splitlines():
        if line.strip() == "## 컨텍스트 목록":
            in_context_list = True
            continue
        if in_context_list and line.startswith("## "):
            break
        if not in_context_list:
            continue
        match = re.search(r"\[(CONTEXT-[^\]]+\.md)\]", line)
        if match:
            names.append(match.group(1))
    return names


def _context_files(session_dir: Path, index_text: str) -> list[Path]:
    contexts = session_dir / "contexts"
    if not contexts.is_dir():
        return []
    by_name = {path.name: path for path in contexts.glob("CONTEXT-*.md")}
    ordered = [by_name[name] for name in _context_names_from_index(index_text) if name in by_name]
    ordered_names = {path.name for path in ordered}
    remaining = sorted(
        (path for name, path in by_name.items() if name not in ordered_names),
        key=lambda path: path.name,
        reverse=True,
    )
    return ordered + remaining


def _recent_context_files(context_files: list[Path], limit: int = 3) -> list[Path]:
    if len(context_files) <= limit:
        return context_files
    names = [path.name for path in context_files]
    if names == sorted(names):
        return context_files[-limit:]
    return context_files[:limit]


def _clip(text: str, budget_chars: int) -> str:
    if budget_chars <= 0:
        return ""
    if len(text) <= budget_chars:
        return text
    if budget_chars <= len(TRUNCATION_MARKER):
        return text[:budget_chars]
    return text[: budget_chars - len(TRUNCATION_MARKER)].rstrip() + TRUNCATION_MARKER


def _is_meaningful_file_path(value: str) -> bool:
    if value in PLACEHOLDER_FILE_VALUES:
        return False
    if value.startswith(("/", "~")):
        return False
    if value.startswith(("./", "../")):
        return False
    return any(part for part in Path(value).parts)


def _extract_file_evidence(text: str) -> list[str]:
    files = []
    in_files = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            in_files = stripped.lower() == "### files"
            continue
        if in_files and stripped.startswith("#"):
            in_files = False
        if not in_files or not stripped.startswith("- "):
            continue
        candidate = stripped[2:].strip()
        if _is_meaningful_file_path(candidate):
            files.append(candidate)
    return files


def _sanitize_context_text(text: str) -> str:
    lines = []
    in_files = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            in_files = stripped.lower() == "### files"
            lines.append(line)
            continue
        if in_files and stripped.startswith("#"):
            in_files = False
        if in_files and stripped.startswith("- ") and stripped[2:].strip() in PLACEHOLDER_FILE_VALUES:
            continue
        lines.append(line)
    return "\n".join(lines)


def _section_budget(total_budget: int, requested: int, floor: int) -> int:
    return max(floor, min(requested, total_budget))


def build_resume_prompt(session_dir: Path, budget_chars: int = 8000) -> str:
    if budget_chars <= len(MINIMAL_PROMPT):
        return MINIMAL_PROMPT[:budget_chars]
    if budget_chars <= max(MIN_STRUCTURED_PROMPT_BUDGET, MIN_SMALL_BUDGET_WITH_TAGS):
        return MINIMAL_PROMPT
    if budget_chars <= len(STRUCTURED_PROMPT_EMPTY):
        return MINIMAL_PROMPT

    index_path = session_dir / "INDEX.md"
    index_text = index_path.read_text() if index_path.is_file() else ""
    files = []
    context_chunks = []
    for path in _recent_context_files(_context_files(session_dir, index_text)):
        text = path.read_text()
        context_chunks.append(f"--- {path.name} ---\n{_sanitize_context_text(text)}")
        files.extend(_extract_file_evidence(text))
    files_text = "\n".join(f"- {item}" for item in sorted(set(files))[:20]) or "- no file evidence recorded"
    fixed_budget = len(STRUCTURED_PROMPT_EMPTY)
    content_budget = max(0, budget_chars - fixed_budget)
    index_budget = _section_budget(content_budget // 4, 1200, 80)
    files_budget = _section_budget(content_budget // 4, 1200, 80)
    next_budget = max(120, content_budget - index_budget - files_budget)
    index_section = _clip(index_text, index_budget)
    files_section = _clip(files_text, files_budget)
    next_section = _clip("\n\n".join(context_chunks), next_budget)
    fields = [
        "<codex-session-memory>",
        "current_goal: 이어진 Codex 작업 맥락을 복원한다.",
        "last_known_state:",
        index_section,
        "files_and_branches:",
        files_section,
        "next_action:",
        next_section,
        "</codex-session-memory>",
    ]
    prompt = "\n".join(fields)
    if len(prompt) <= budget_chars:
        return prompt
    for section_index in (7, 5, 3):
        if len(prompt) <= budget_chars:
            break
        overflow = len(prompt) - budget_chars
        fields[section_index] = _clip(fields[section_index], max(0, len(fields[section_index]) - overflow))
        prompt = "\n".join(fields)
    if len(prompt) <= budget_chars:
        return prompt
    return MINIMAL_PROMPT
