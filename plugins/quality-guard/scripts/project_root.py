"""Project root resolution for quality-guard.

Mirrors session-memory's helper to keep behavior consistent. The two
plugins are distributed independently, so cross-imports are forbidden;
each plugin carries its own copy.
"""
# NOTE: This file is duplicated between session-memory and quality-guard.
# Plugins ship independently so cross-import is forbidden. If you change
# `find_project_root` or `_git_toplevel`, update BOTH copies.
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


def find_project_root(cwd: str) -> str:
    """Resolve the canonical project root.

    Priority:
    1. CLAUDE_PROJECT_DIR env var (Claude Code official, stable across cd).
    2. Topmost ancestor of cwd containing a .claude/ directory.
    3. git rev-parse --show-toplevel from cwd.
    4. cwd itself.

    Why topmost (not nearest) .claude/: in monorepos, users place .claude/
    at the workspace root, so writes from any sub-package must consolidate
    there. The trade-off: if a developer dogfoods a plugin on a nested
    project that has its own .claude/, this walk picks the outer root.
    Set CLAUDE_PROJECT_DIR (tier 1) to override in that case.
    """
    env = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if env and Path(env).is_dir():
        return str(Path(env).resolve())

    path = Path(cwd).resolve()
    topmost = None
    for candidate in [path] + list(path.parents):
        if (candidate / ".claude").is_dir():
            topmost = candidate
    if topmost:
        return str(topmost)

    git_top = _git_toplevel(cwd)
    if git_top:
        return git_top

    return str(path)
