from __future__ import annotations


def prefixed(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}"


__all__ = ["prefixed"]
