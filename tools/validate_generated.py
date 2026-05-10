from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.validators import validate_generated_headers, validate_marketplaces


def main() -> int:
    """Validate generated plugin artifacts without rewriting them."""

    errors = []
    errors.extend(validate_marketplaces(ROOT))
    errors.extend(validate_generated_headers(ROOT))
    if errors:
        for error in errors:
            print(error)
        return 1

    print("generated artifacts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
