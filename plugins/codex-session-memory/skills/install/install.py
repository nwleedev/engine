#!/usr/bin/env python3
import importlib.util
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"


def _load_script_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


csm_dotenv_loader = _load_script_module(
    "dotenv_loader.py", "codex_session_memory_install_dotenv_loader"
)
csm_project_root = _load_script_module(
    "project_root.py", "codex_session_memory_install_project_root"
)
csm_agents_rules = _load_script_module(
    "agents_rules.py", "codex_session_memory_install_agents_rules"
)


def main(argv=None):
    if argv:
        print("usage: install.py", file=sys.stderr)
        return 2

    cwd = os.getcwd()
    csm_dotenv_loader.load_project_dotenv(cwd)
    root = csm_project_root.find_project_root(cwd)
    report = csm_agents_rules.check_agents_rules(root)

    print(f"Project root: {root}")
    print(f"AGENTS.md: {report.agents_path}")
    print(f"status: {report.status}")
    if report.missing:
        print("missing markers:")
        for marker in report.missing:
            print(f"- {marker}")
    if report.patch:
        print("")
        print(report.patch)
    return 0 if report.status == "installed" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
