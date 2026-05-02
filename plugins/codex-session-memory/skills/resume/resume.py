#!/usr/bin/env python3
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"


MAX_INJECT_CHARS = 8000


def load_script_module(filename: str, module_name: str):
    module_path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dotenv_loader = load_script_module("dotenv_loader.py", "codex_session_memory_resume_dotenv_loader")
pr = load_script_module("project_root.py", "codex_session_memory_resume_project_root")
io = load_script_module("index_io.py", "codex_session_memory_resume_index_io")


def list_sessions(root: str):
    sessions_dir = Path(root) / ".codex" / "sessions"
    if not sessions_dir.is_dir():
        return []
    rows = []
    for d in sessions_dir.iterdir():
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        idx = d / "INDEX.md"
        if not idx.is_file():
            continue
        fm = io.read_frontmatter(idx) or {}
        rows.append({
            "session_id": fm.get("session_id", d.name),
            "last_updated": fm.get("last_updated", ""),
            "path": idx,
        })
    rows.sort(key=lambda r: str(r["last_updated"]), reverse=True)
    return rows[:10]


def render_table(rows):
    if not rows:
        return "(no sessions found in <root>/.codex/sessions/)"
    out = ["| # | session_id (8) | last_updated |", "|---|---|---|"]
    for i, r in enumerate(rows, 1):
        sid = str(r["session_id"])[:8]
        out.append(f"| {i} | {sid} | {r['last_updated']} |")
    out.append("")
    out.append("Call `$codex-session-memory:resume <8-char-prefix>` to inject one.")
    return "\n".join(out)


def main(argv):
    cwd = os.getcwd()
    dotenv_loader.load_project_dotenv(cwd)
    root = pr.find_project_root(cwd)

    if len(argv) <= 1:
        print(render_table(list_sessions(root)))
        return 0

    prefix = argv[1]
    matches = [r for r in list_sessions(root) if str(r["session_id"]).startswith(prefix)]
    if not matches:
        print(f"error: no session matches prefix '{prefix}'", file=sys.stderr)
        return 2
    target_session_dir = matches[0]["path"].parent
    resume_prompt = load_script_module("resume_prompt.py", "codex_session_memory_resume_prompt")
    print(resume_prompt.build_resume_prompt(target_session_dir, budget_chars=MAX_INJECT_CHARS))
    print(f"Inspect <root>/.codex/sessions/{matches[0]['session_id']}/contexts/*.md for full details.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
