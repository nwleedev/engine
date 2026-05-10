from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.validators import validate_marketplaces


def main() -> int:
    """Validate generated plugin marketplace artifacts."""

    errors = validate_marketplaces(ROOT)
    if errors:
        for error in errors:
            print(error)
        return 1

    print("generated artifacts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
