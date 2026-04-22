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
    cwd = payload.get("cwd", "") or os.getcwd()
    from compress_feedback import run_compression
    run_compression(cwd)


if __name__ == "__main__":
    main()
