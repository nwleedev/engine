#!/usr/bin/env python3
"""Best-effort raw evidence checkpoint marker hook."""
import sys


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
