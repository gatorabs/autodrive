"""Generic helpers for dealing with control values."""
from __future__ import annotations

from typing import Any


def prefixed(prefix: str, suffix: str) -> str:
    """Compose a prefixed key name used in shared control dictionaries."""
    return f"{prefix}_{suffix}"


def safe_int(value: Any, default: int = 0) -> int:
    """Safely cast *value* to ``int`` returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_speed(value: Any, lo: int = 0, hi: int = 255) -> int:
    """Clamp a numeric value to the valid speed range."""
    coerced = safe_int(value, lo)
    return max(lo, min(hi, coerced))


__all__ = ["clamp_speed", "prefixed", "safe_int"]
