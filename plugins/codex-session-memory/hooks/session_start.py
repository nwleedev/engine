#!/usr/bin/env python3
"""Inject saved Codex session memory at session start."""
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
SCRIPTS = PLUGIN / "scripts"
MAX_INJECT_CHARS = 8000


def _load_script_module(filename: str, module_name: str):
    module_path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    return payload if isinstance(payload, dict) else {}


def _print_context(prompt: str) -> None:
    if not prompt.strip():
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": prompt,
        }
    }))


def main() -> int:
    try:
        payload = _read_payload()
        if payload.get("source") == "clear":
            return 0

        dotenv_loader = _load_script_module("dotenv_loader.py", "codex_session_memory_hook_dotenv_loader")
        project_root = _load_script_module("project_root.py", "codex_session_memory_hook_project_root")
        session_locator = _load_script_module("session_locator.py", "codex_session_memory_hook_session_locator")
        resume_prompt = _load_script_module("resume_prompt.py", "codex_session_memory_hook_resume_prompt")

        cwd = str(payload.get("cwd") or Path.cwd())
        thread_id = str(payload.get("session_id") or "").strip() or session_locator.current_thread_id()
        if not thread_id:
            return 0

        dotenv_loader.load_project_dotenv(cwd)
        root = project_root.find_project_root(cwd)
        session_dir = session_locator.data_session_dir(root, thread_id)
        if not session_dir.is_dir():
            return 0

        _print_context(resume_prompt.build_resume_prompt(session_dir, budget_chars=MAX_INJECT_CHARS))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
