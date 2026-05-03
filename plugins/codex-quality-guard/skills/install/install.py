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


cqg_project_root = _load_script_module(
    "project_root.py", "codex_quality_guard_install_project_root"
)
cqg_agents_rules = _load_script_module(
    "agents_rules.py", "codex_quality_guard_install_agents_rules"
)


def main(argv=None):
    args = [] if argv is None else list(argv)
    if len(args) > 1 or (args and args[0] not in {"en", "ko"}):
        print("usage: install.py [en|ko]", file=sys.stderr)
        return 2
    locale = args[0] if args else None

    root = cqg_project_root.find_project_root(os.getcwd())
    report = cqg_agents_rules.check_agents_rules(root, locale=locale)

    print(f"Project root: {root}")
    print(f"AGENTS.md: {report.agents_path}")
    print(f"status: {report.status}")
    if report.missing:
        print("missing markers:")
        for marker in report.missing:
            print(f"- {marker}")
    if report.guidance:
        print("")
        print("guidance:")
        print(report.guidance)
    return 0 if report.status == "installed" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
