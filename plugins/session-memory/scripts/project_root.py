"""Project root resolution with git-toplevel-first policy and monorepo guard."""
# NOTE: This file is duplicated between session-memory and quality-guard.
# Plugins ship independently so cross-import is forbidden. If you change
# `find_project_root` or `_git_toplevel`, update BOTH copies.
import os
import subprocess
from pathlib import Path
from typing import List


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


def assert_root_is_canonical(resolved_root: "str | Path", cwd: "str | Path") -> None:
    """Refuse to write to non-git-toplevel locations inside a git repo.

    Skip the git check when CLAUDE_PROJECT_DIR is set AND it points at the
    resolved_root being passed in. The env var is the explicit declaration
    of the canonical root and legitimately diverges from git toplevel in
    monorepos with nested git repositories. If env is set but does not
    match resolved_root, fall through — the caller has likely passed a
    stale or wrong path.
    """
    env = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if env and Path(env).resolve() == Path(resolved_root).resolve():
        return
    git_top = _git_toplevel(str(cwd))
    if git_top and Path(git_top).resolve() != Path(resolved_root).resolve():
        raise RuntimeError(
            f"refuse to write to {resolved_root}: not git toplevel ({git_top})"
        )


def detect_subpackage_pollution(repo_root: "str | Path") -> List[Path]:
    """Find .claude/ directories nested under repo_root (not the root one)."""
    repo_root = Path(repo_root).resolve()
    found = []
    for claude in repo_root.rglob(".claude"):
        if not claude.is_dir():
            continue
        if claude.parent.resolve() == repo_root:
            continue
        found.append(claude)
    return found
