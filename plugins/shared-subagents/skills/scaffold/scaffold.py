#!/usr/bin/env python3
"""Run shared-subagents scaffold helpers from the plugin cache location."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent.parent
SCRIPTS = PLUGIN_ROOT / "scripts"


def _load_script_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


installer = _load_script_module(
    "install_shared_subagents.py", "shared_subagents_scaffold_installer"
)
block_printer = _load_script_module(
    "print_agents_md_block.py", "shared_subagents_scaffold_block_printer"
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse scaffold command arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=installer.default_project_root())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--print-agents-md-block", action="store_true")
    return parser.parse_args(argv)


def print_targets(targets: list[Path], mode: str) -> None:
    """Print install target paths using the shared installer output format."""

    for target in targets:
        print(f"{mode}: {target}")


def main(argv: list[str] | None = None) -> int:
    """Run scaffold actions from any current working directory."""

    args = parse_args([] if argv is None else argv)
    if args.print_agents_md_block:
        print(block_printer.read_block(), end="")
        return 0

    dry_run = args.dry_run or not args.install
    targets = installer.install_agents(
        args.project_root.expanduser(),
        dry_run,
        force=args.force,
        backup=args.backup,
    )
    print_targets(targets, "would install" if dry_run else "installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
