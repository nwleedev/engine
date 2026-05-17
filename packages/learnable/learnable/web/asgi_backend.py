from __future__ import annotations


def preflight() -> dict[str, object]:
    """Report optional ASGI backend availability for future Learnable versions."""

    return {
        "available": False,
        "reason": "optional ASGI backend is not implemented in the MVP",
    }
