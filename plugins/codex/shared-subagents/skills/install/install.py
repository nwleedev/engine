# GENERATED FILE - DO NOT EDIT
# source: plugin-sources/shared-subagents/skills/install/install.py

#!/usr/bin/env python3
"""Install shared Codex subagent TOML files into a project .codex directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


AGENT_NAMES = (
    "context-manager.toml",
    "code-mapper.toml",
    "docs-researcher.toml",
    "source-researcher.toml",
    "requirements-reviewer.toml",
    "plan-reviewer.toml",
    "spec-coverage-reviewer.toml",
    "citation-verifier.toml",
    "test-reconciliation-reviewer.toml",
    "test-adequacy-reviewer.toml",
    "closure-reviewer.toml",
    "completion-claim-reviewer.toml",
    "risk-reviewer.toml",
    "reviewer.toml",
    "code-reviewer.toml",
    "security-auditor.toml",
)


def plugin_root() -> Path:
    """Return the plugin root based on this skill helper location."""

    return Path(__file__).resolve().parents[2]


def default_project_root() -> Path:
    """Return the default project root directory."""

    return Path.cwd()


def backup_path_for(target: Path) -> Path:
    """Return the first available backup path for an existing target."""

    candidate = target.with_name(f"{target.name}.bak")
    if not candidate.exists():
        return candidate

    index = 1
    while True:
        candidate = target.with_name(f"{target.name}.bak{index}")
        if not candidate.exists():
            return candidate
        index += 1


def install_agents(
    project_root: Path,
    dry_run: bool,
    *,
    force: bool = False,
    backup: bool = False,
) -> list[Path]:
    """Copy bundled agent TOML files into the project-local Codex agents directory."""

    source_dir = plugin_root() / "agents"
    target_dir = project_root / ".codex" / "agents"
    installed: list[Path] = []

    for name in AGENT_NAMES:
        source = source_dir / name
        target = target_dir / name
        if not source.exists():
            raise FileNotFoundError(f"missing bundled agent: {source}")
        installed.append(target)
        if dry_run:
            continue
        if target.exists() and not force and not backup:
            raise FileExistsError(
                f"target already exists: {target}; use --backup or --force"
            )
        target_dir.mkdir(parents=True, exist_ok=True)
        if target.exists() and backup:
            backup_target = backup_path_for(target)
            shutil.copy2(target, backup_target)
            print(f"backed up: {backup_target}")
        shutil.copy2(source, target)

    return installed


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=default_project_root())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--backup", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Install shared subagents into the project-local .codex directory."""

    args = parse_args()
    dry_run = args.dry_run or not args.install
    targets = install_agents(
        args.project_root.expanduser().resolve(),
        dry_run,
        force=args.force,
        backup=args.backup,
    )
    mode = "would install" if dry_run else "installed"
    for target in targets:
        print(f"{mode}: {target}")
    if not dry_run:
        print("restart required: Codex must be restarted before new agents are expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
