"""Project root resolution for codex-session-memory.

6-tier resolution priority:
1. CODEX_PROJECT_DIR env var (must be existing directory).
2. Same env var, populated earlier by dotenv_loader.
3. Topmost ancestor with AGENTS.md (HOME boundary).
4. Topmost ancestor with .codex/ (HOME boundary).
5. git rev-parse --show-toplevel.
6. cwd.
"""
import os
import subprocess
from pathlib import Path


def _git_toplevel(cwd: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=3,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _topmost_ancestor_with(path: Path, marker: str, home: Path, must_be_file: bool = False):
    topmost = None
    for candidate in [path] + list(path.parents):
        if candidate == home:
            break
        target = candidate / marker
        if must_be_file:
            if target.is_file():
                topmost = candidate
        else:
            if target.exists():
                topmost = candidate
    return topmost


def find_project_root(cwd: str) -> str:
    env = os.environ.get("CODEX_PROJECT_DIR", "").strip()
    if env and Path(env).is_dir():
        return str(Path(env).resolve())

    path = Path(cwd).resolve()
    home = Path.home().resolve()

    top = _topmost_ancestor_with(path, "AGENTS.md", home, must_be_file=True)
    if top:
        return str(top)

    top = _topmost_ancestor_with(path, ".codex", home)
    if top and (top / ".codex").is_dir():
        return str(top)

    git_top = _git_toplevel(cwd)
    if git_top:
        return git_top

    return str(path)


def assert_root_is_canonical(resolved_root, cwd) -> None:
    env = os.environ.get("CODEX_PROJECT_DIR", "").strip()
    if env and Path(env).resolve() == Path(resolved_root).resolve():
        return
    git_top = _git_toplevel(str(cwd))
    if git_top and Path(git_top).resolve() != Path(resolved_root).resolve():
        raise RuntimeError(
            f"refuse to write to {resolved_root}: not git toplevel ({git_top}). "
            f"Set CODEX_PROJECT_DIR in shell or .env to override."
        )
