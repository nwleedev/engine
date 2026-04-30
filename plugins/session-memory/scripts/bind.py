"""Print a settings.local.json snippet that pins CLAUDE_PROJECT_DIR.

Slash-command companion. No file writes — output only.
"""
import json
import os
import sys
from pathlib import Path

import project_root


def _resolve_target(arg: str | None, cwd: str) -> Path:
    if arg:
        p = Path(arg).expanduser().resolve()
        if not p.is_dir():
            raise SystemExit(f"bind: path is not a directory: {p}")
        return p
    # Ignore CLAUDE_PROJECT_DIR for auto-detect (the whole point is the user
    # may have it wrong or unset). Force fresh resolution from cwd.
    saved = os.environ.pop("CLAUDE_PROJECT_DIR", None)
    try:
        return Path(project_root.find_project_root(cwd)).resolve()
    finally:
        if saved is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = saved


def _render(target: Path) -> str:
    body = json.dumps({"env": {"CLAUDE_PROJECT_DIR": str(target)}}, indent=2)
    inline = json.dumps({"CLAUDE_PROJECT_DIR": str(target)}, indent=2)
    settings_path = target / ".claude" / "settings.local.json"
    bar = "=" * 62
    return (
        f"{bar}\n"
        f"session-memory: bind project root\n"
        f"{bar}\n\n"
        f"Target file : {settings_path}\n"
        f"Value       : CLAUDE_PROJECT_DIR = {target}\n\n"
        f"---- New / empty file -----------------------------------------\n"
        f"{body}\n\n"
        f"---- Merge into existing file (add/merge `env` key) ----------\n"
        f'"env": {inline}\n\n'
        f"After saving, exit Claude completely and relaunch.\n\n"
        f"(macOS quick copy)\n"
        f"pbcopy <<'EOF'\n"
        f"{body}\n"
        f"EOF\n"
        f"{bar}\n"
    )


def main(argv: list[str], cwd: str) -> int:
    arg = argv[1] if len(argv) > 1 else None
    try:
        target = _resolve_target(arg, cwd)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 1
    sys.stdout.write(_render(target))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv, os.getcwd()))
