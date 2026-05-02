#!/usr/bin/env python3
"""Best-effort raw evidence checkpoint marker hook."""
import os
import sys


INTERNAL_ENV = "CODEX_SESSION_MEMORY_INTERNAL"


def main() -> int:
    if os.environ.get(INTERNAL_ENV):
        return 0

    try:
        sys.stdin.read()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
