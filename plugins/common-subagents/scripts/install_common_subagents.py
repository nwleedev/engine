#!/usr/bin/env python3
"""Install common Codex subagent TOML files into a Codex home directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


AGENT_NAMES = (
    "context-manager.toml",
    "code-mapper.toml",
    "docs-researcher.toml",
    "spec-reviewer.toml",
    "reviewer.toml",
    "code-reviewer.toml",
    "security-auditor.toml",
    "online-researcher.toml",
)


def plugin_root() -> Path:
    """Return the plugin root based on this script location."""

    return Path(__file__).resolve().parents[1]


def default_codex_home() -> Path:
    """Return the default Codex home directory."""

    return Path.home() / ".codex"


def install_agents(codex_home: Path, dry_run: bool) -> list[Path]:
    """Copy bundled agent TOML files into the Codex agents directory."""

    source_dir = plugin_root() / "agents"
    target_dir = codex_home / "agents"
    installed: list[Path] = []

    for name in AGENT_NAMES:
        source = source_dir / name
        target = target_dir / name
        if not source.exists():
            raise FileNotFoundError(f"missing bundled agent: {source}")
        installed.append(target)
        if dry_run:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    return installed


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", type=Path, default=default_codex_home())
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Install common subagents and print installed target paths."""

    args = parse_args()
    targets = install_agents(args.codex_home.expanduser(), args.dry_run)
    mode = "would install" if args.dry_run else "installed"
    for target in targets:
        print(f"{mode}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
