import subprocess
from pathlib import Path

_MAX_FILE_CHARS = 2000
_GIT_LOG_LIMIT = 10


def _read_file(path: Path, max_chars: int = _MAX_FILE_CHARS) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
        return text[:max_chars] if len(text) > max_chars else text
    except OSError:
        return None


def _read_git_log(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", f"-{_GIT_LOG_LIMIT}", "--oneline"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def read_project_files(cwd: str) -> str:
    """Return concatenated project context string for LLM domain inference."""
    root = Path(cwd)
    parts: list[str] = []

    # Empty files are omitted (empty string is falsy — no LLM context to provide)
    readme = _read_file(root / "README.md")
    if readme:
        parts.append(f"## README.md\n{readme}")

    claude_md = _read_file(root / "CLAUDE.md")
    if claude_md:
        parts.append(f"## CLAUDE.md\n{claude_md}")

    git_log = _read_git_log(cwd)
    if git_log:
        parts.append(f"## Recent git commits\n{git_log}")

    return "\n\n".join(parts)
