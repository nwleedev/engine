#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def main() -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    cwd_raw = payload.get("cwd", "") or os.getcwd()
    from project_root import find_project_root
    cwd = find_project_root(cwd_raw)
    from quality_analyzer import run_quality_analysis
    run_quality_analysis(payload, cwd)


if __name__ == "__main__":
    main()
