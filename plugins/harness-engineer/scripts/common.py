# plugins/harness-engineer/scripts/common.py
import os
import subprocess
from pathlib import Path


def find_project_root(cwd: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    path = Path(cwd)
    for candidate in [path] + list(path.parents):
        if (candidate / ".claude").is_dir():
            return str(candidate)
    return cwd


def resolve_cwd(payload: dict) -> str:
    return (
        payload.get("cwd", "")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
        or os.environ.get("PWD", "")
    )


def get_harness_dir(project_root: str) -> Path:
    return Path(project_root) / ".claude" / "harness"


def detect_language(text: str) -> str:
    """Detect language from text using Korean Unicode range. No LLM needed."""
    if not text:
        return "en"
    korean_chars = sum(1 for c in text if '\uAC00' <= c <= '\uD7A3')
    return "ko" if korean_chars / max(len(text), 1) > 0.1 else "en"


def get_harness_language(default: str = "auto") -> str:
    return os.environ.get("HARNESS_LANGUAGE", default).strip() or "auto"
