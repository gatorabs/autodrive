"""Utilities for configuring stop/acceleration ramps."""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping


def _as_mapping(ctrls: Any) -> Mapping[str, Any]:
    if isinstance(ctrls, Mapping):
        return ctrls
    if isinstance(ctrls, MutableMapping):  # pragma: no cover - MutableMapping is Mapping
        return ctrls  # type: ignore[return-value]
    return {}


def get_stop_hold_seconds(tk_controls: Any) -> float:
    controls = _as_mapping(tk_controls)
    raw = controls.get("StopHoldSeconds", controls.get("Timestamp", 5))
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 5.0


def get_deceleration_step(tk_controls: Any) -> int:
    controls = _as_mapping(tk_controls)
    try:
        step = int(round(float(controls.get("StopDecelerationStep", 10))))
    except (TypeError, ValueError):
        step = 10
    return max(1, step)


def get_ramp_interval(tk_controls: Any) -> float:
    controls = _as_mapping(tk_controls)
    raw_value = controls.get("StopRampInterval")

    if raw_value is None:
        for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
            if legacy_key in controls:
                raw_value = controls[legacy_key]
                break

    if raw_value is None:
        raw_value = 0.2

    try:
        interval = float(raw_value)
    except (TypeError, ValueError):
        interval = 0.2

    return max(0.0, interval)


__all__ = [
    "get_stop_hold_seconds",
    "get_deceleration_step",
    "get_ramp_interval",
]
