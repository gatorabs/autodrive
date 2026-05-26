"""Utilities for configuring stop/acceleration ramps."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping, cast


def _as_mapping(ctrls: Any) -> Mapping[str, Any]:
    if isinstance(ctrls, Mapping):
        return ctrls
    if isinstance(ctrls, MutableMapping):  # pragma: no cover - MutableMapping is Mapping
        return ctrls  # type: ignore[return-value]
    getter = getattr(ctrls, "get", None)
    contains = getattr(ctrls, "__contains__", None)
    if callable(getter) and callable(contains):
        return cast(Mapping[str, Any], ctrls)
    return {}


def get_stop_hold_seconds(tk_controls: Any) -> float:
    controls = _as_mapping(tk_controls)
    raw = controls.get("StopHoldSeconds", controls.get("Timestamp", 5))
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 5.0


def _iter_prefixed_keys(base_name: str, prefix: str) -> Iterable[str]:
    trimmed = prefix.rstrip("_")
    yield f"{trimmed}{base_name}"
    yield f"{trimmed}_{base_name}"


def get_deceleration_step(tk_controls: Any, *, key_prefix: str | None = None) -> int:
    controls = _as_mapping(tk_controls)

    candidate_keys = []
    if key_prefix:
        candidate_keys.extend(_iter_prefixed_keys("StopDecelerationStep", key_prefix))
    candidate_keys.append("StopDecelerationStep")

    for key in candidate_keys:
        if key not in controls:
            continue
        try:
            step = int(round(float(controls[key])))
        except (TypeError, ValueError):
            continue
        return max(1, step)

    return 10


def get_ramp_interval(tk_controls: Any, *, key_prefix: str | None = None) -> float:
    controls = _as_mapping(tk_controls)

    candidate_keys = []
    if key_prefix:
        candidate_keys.extend(_iter_prefixed_keys("StopRampInterval", key_prefix))
    candidate_keys.append("StopRampInterval")
    candidate_keys.extend(("StopDecelerationInterval", "StopAccelerationInterval"))

    for key in candidate_keys:
        if key not in controls:
            continue
        try:
            interval = float(controls[key])
        except (TypeError, ValueError):
            continue
        return max(0.0, interval)

    return 0.2


__all__ = [
    "get_stop_hold_seconds",
    "get_deceleration_step",
    "get_ramp_interval",
]
