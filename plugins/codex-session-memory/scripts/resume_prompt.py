"""Build compact SessionStart context from saved session memory."""
from pathlib import Path


def _context_files(session_dir: Path) -> list[Path]:
    contexts = session_dir / "contexts"
    if not contexts.is_dir():
        return []
    return sorted(contexts.glob("CONTEXT-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def _clip(text: str, budget_chars: int) -> str:
    if len(text) <= budget_chars:
        return text
    return text[: budget_chars - 40].rstrip() + "\n...[truncated for Codex context budget]"


def build_resume_prompt(session_dir: Path, budget_chars: int = 8000) -> str:
    index_path = session_dir / "INDEX.md"
    index_text = index_path.read_text() if index_path.is_file() else ""
    latest_context = ""
    files = []
    for path in _context_files(session_dir)[:3]:
        text = path.read_text()
        latest_context += f"\n\n--- {path.name} ---\n{text}"
        for line in text.splitlines():
            if line.startswith("- plugins/") or line.startswith("- tests/") or line.startswith("- docs/"):
                files.append(line[2:])
    fields = [
        "<codex-session-memory>",
        "current_goal: 이어진 Codex 작업 맥락을 복원한다.",
        "last_known_state:",
        _clip(index_text, 1600),
        "files_and_branches:",
        "\n".join(f"- {item}" for item in sorted(set(files))[:20]) or "- 저장된 파일 근거 없음",
        "next_action:",
        _clip(latest_context, max(1000, budget_chars - 2600)),
        "</codex-session-memory>",
    ]
    return _clip("\n".join(fields), budget_chars)
