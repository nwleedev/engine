"""Project root resolution for codex-quality-guard."""
import os
import subprocess
from pathlib import Path


def _git_toplevel(cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _topmost_ancestor_with_agents(path: Path, home: Path) -> Path | None:
    topmost = None
    for candidate in [path] + list(path.parents):
        if candidate == home:
            break
        if (candidate / "AGENTS.md").is_file():
            topmost = candidate
    return topmost


def find_project_root(cwd: str) -> str:
    env = os.environ.get("CODEX_PROJECT_DIR", "").strip()
    if env and Path(env).is_dir():
        return str(Path(env).resolve())

    git_top = _git_toplevel(cwd)
    if git_top:
        return git_top

    path = Path(cwd).resolve()
    top = _topmost_ancestor_with_agents(path, Path.home().resolve())
    if top:
        return str(top)

    return str(path)
