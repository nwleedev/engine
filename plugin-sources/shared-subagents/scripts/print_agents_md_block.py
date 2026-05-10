#!/usr/bin/env python3
"""Print the AGENTS.md guidance block for common subagents."""

from __future__ import annotations

from pathlib import Path


def block_path() -> Path:
    """Return the bundled AGENTS.md block path."""

    return Path(__file__).resolve().parents[1] / "references" / "agents-md-block.md"


def read_block() -> str:
    """Read the copy-paste block without modifying any repository file."""

    return block_path().read_text(encoding="utf-8")


def main() -> int:
    """Print the AGENTS.md block to stdout."""

    print(read_block(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
