#!/usr/bin/env python3
"""Best-effort raw evidence checkpoint marker hook."""
import json
import sys


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
