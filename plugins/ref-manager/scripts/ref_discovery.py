"""ref_discovery — protocol contract for finding project refs.

External plugins that need to list registered refs (e.g. quality-guard)
should read `.claude/refs/INDEX.md` directly rather than importing this
module, to avoid a cross-plugin import dependency.

Storage contract (stable):
  <cwd>/.claude/refs/INDEX.md   — markdown table, columns: Name | Path | Tags
  <cwd>/.claude/refs/<topic>/   — one subdirectory per topic, holds the actual files

Discovery:
  Use load_index(cwd) from ref_io to get parsed entries as list[dict]:
    {"name": str, "path": str, "tags": list[str]}
  path is relative to <cwd>.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ref_io import load_index

REFS_DIR_NAME = ".claude/refs"
INDEX_FILE_NAME = "INDEX.md"


def refs_dir(cwd: str) -> Path:
    return Path(cwd) / REFS_DIR_NAME


def index_path(cwd: str) -> Path:
    return refs_dir(cwd) / INDEX_FILE_NAME


def has_refs(cwd: str) -> bool:
    """Return True if the project has a non-empty refs index."""
    return bool(load_index(cwd))
