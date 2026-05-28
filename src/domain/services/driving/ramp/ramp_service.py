"""Shared ramp/deceleration helpers for stop-aware services."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.domain.services.driving.control.control_value_service import clamp_speed
from src.domain.services.driving.control.state_key_service import prefixed
from src.domain.services.driving.ramp.ramp_settings_service import (
    get_deceleration_step,
    get_ramp_interval,
)


def record_requested_speed(
    shared_controls: Dict[str, Any],
    lane_data,
    *,
    force: bool = False,
    prefix: str = "STOP_SIGN",
) -> None:
    requested_speed = clamp_speed(getattr(lane_data, "car_speed_data", 0))

    if not force:
        decel_state = shared_controls.get(prefixed(prefix, "DECEL_STATE"))
        if decel_state:
            current_speed = clamp_speed(decel_state.get("current_speed", 0))
            if requested_speed == current_speed:
                return

    shared_controls[prefixed(prefix, "PREV_SPEED")] = requested_speed


def start_deceleration(
    shared_controls: Dict[str, Any],
    initial_speed: Any,
    tk_controls: Any,
    current_time: float,
    *,
    prefix: str = "STOP_SIGN",
    target_speed: int = 0,
    control_key_prefix: str | None = None,
) -> None:
    step = get_deceleration_step(tk_controls, key_prefix=control_key_prefix)
    interval = get_ramp_interval(tk_controls, key_prefix=control_key_prefix)

    starting_speed = clamp_speed(initial_speed)
    desired_target = clamp_speed(target_speed)
    desired_target = max(0, min(starting_speed, desired_target))

    shared_controls[prefixed(prefix, "DECEL_STATE")] = {
        "current_speed": starting_speed,
        "target_speed": desired_target,
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,
    }


def _ensure_hold_timer(
    shared_controls: Dict[str, Any],
    current_time: float,
    *,
    prefix: str = "STOP_SIGN",
) -> None:
    key_hold = prefixed(prefix, "HOLD_SECONDS")
    key_resume = prefixed(prefix, "RESUME_TIME")
    key_active = prefixed(prefix, "ACTIVE")

    hold_seconds = float(shared_controls.get(key_hold, 0.0) or 0.0)
    resume_time = shared_controls.get(key_resume)

    if hold_seconds <= 0.0:
        shared_controls[key_active] = False
        shared_controls[key_resume] = current_time
        return

    if resume_time is None:
        shared_controls[key_resume] = current_time + hold_seconds
        shared_controls[key_active] = True
        return

    shared_controls[key_active] = current_time < resume_time


def apply_deceleration(
    shared_controls: Dict[str, Any],
    tk_controls: Any,
    current_time: float,
    *,
    prefix: str = "STOP_SIGN",
    control_key_prefix: str | None = None,
) -> int:
    state = shared_controls.get(prefixed(prefix, "DECEL_STATE"))
    if not state:
        return 0

    current_speed = clamp_speed(state.get("current_speed", 0))
    target_speed = clamp_speed(state.get("target_speed", 0))

    slider_step = get_deceleration_step(tk_controls, key_prefix=control_key_prefix)
    step = state.get("step")
    if not isinstance(step, int) or step != slider_step:
        step = slider_step
        state["step"] = step

    slider_interval = get_ramp_interval(tk_controls, key_prefix=control_key_prefix)
    interval = state.get("interval")
    if not isinstance(interval, (int, float)) or interval != slider_interval:
        interval = slider_interval
        state["interval"] = interval

    if current_speed <= target_speed:
        state["current_speed"] = target_speed
        shared_controls[prefixed(prefix, "DECEL_STATE")] = state
        _ensure_hold_timer(shared_controls, current_time, prefix=prefix)
        return target_speed

    last_update = state.get("last_update")
    if not isinstance(last_update, (int, float)):
        last_update = current_time - interval

    if interval > 0 and current_time - last_update < interval:
        state["last_update"] = last_update
        shared_controls[prefixed(prefix, "DECEL_STATE")] = state
        return current_speed

    next_speed = max(current_speed - step, target_speed)
    state["current_speed"] = next_speed
    state["last_update"] = current_time
    shared_controls[prefixed(prefix, "DECEL_STATE")] = state

    if next_speed <= target_speed:
        state["current_speed"] = target_speed
        shared_controls[prefixed(prefix, "DECEL_STATE")] = state
        _ensure_hold_timer(shared_controls, current_time, prefix=prefix)
        return target_speed

    return next_speed


def start_acceleration(
    shared_controls: Dict[str, Any],
    current_speed: Any,
    target_speed: Any,
    tk_controls: Any,
    current_time: float,
    *,
    prefix: str = "STOP_SIGN",
    control_key_prefix: str | None = None,
) -> None:
    step = get_deceleration_step(tk_controls, key_prefix=control_key_prefix)
    interval = get_ramp_interval(tk_controls, key_prefix=control_key_prefix)

    desired_speed = clamp_speed(target_speed)
    last_output = shared_controls.get(prefixed(prefix, "LAST_SPEED"))
    if last_output is None:
        last_output = current_speed

    starting_speed = clamp_speed(last_output)
    starting_speed = max(0, min(desired_speed, starting_speed))

    if desired_speed <= 0:
        shared_controls.pop(prefixed(prefix, "ACCEL_STATE"), None)
        return

    shared_controls[prefixed(prefix, "ACCEL_STATE")] = {
        "current_speed": starting_speed,
        "target_speed": desired_speed,
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,
    }


def apply_acceleration(
    shared_controls: Dict[str, Any],
    tk_controls: Any,
    current_time: float,
    *,
    prefix: str = "STOP_SIGN",
    control_key_prefix: str | None = None,
) -> Optional[Tuple[int, bool]]:
    state = shared_controls.get(prefixed(prefix, "ACCEL_STATE"))
    if not state:
        return None

    target_speed = clamp_speed(state.get("target_speed", 0))

    latest_target = shared_controls.get(prefixed(prefix, "PREV_SPEED"))
    if latest_target is not None:
        latest_target_int = clamp_speed(latest_target)
        if latest_target_int != target_speed:
            target_speed = latest_target_int
            state["target_speed"] = target_speed

    current_speed = clamp_speed(state.get("current_speed", 0))

    slider_step = get_deceleration_step(tk_controls, key_prefix=control_key_prefix)
    step = state.get("step")
    if not isinstance(step, int) or step != slider_step:
        step = slider_step
        state["step"] = step

    slider_interval = get_ramp_interval(tk_controls, key_prefix=control_key_prefix)
    interval = state.get("interval")
    if not isinstance(interval, (int, float)) or interval != slider_interval:
        interval = slider_interval
        state["interval"] = interval

    if target_speed <= 0 or current_speed >= target_speed:
        shared_controls.pop(prefixed(prefix, "ACCEL_STATE"), None)
        return target_speed, True

    last_update = state.get("last_update")
    if not isinstance(last_update, (int, float)):
        last_update = current_time - interval

    if interval > 0 and current_time - last_update < interval:
        state["last_update"] = last_update
        shared_controls[prefixed(prefix, "ACCEL_STATE")] = state
        return current_speed, False

    next_speed = min(current_speed + step, target_speed)
    state["current_speed"] = next_speed
    state["last_update"] = current_time

    if next_speed >= target_speed:
        shared_controls.pop(prefixed(prefix, "ACCEL_STATE"), None)
        return target_speed, True

    shared_controls[prefixed(prefix, "ACCEL_STATE")] = state
    return next_speed, False


def clear_stop_state(shared_controls: Dict[str, Any], *, prefix: str = "STOP_SIGN") -> None:
    shared_controls.pop(prefixed(prefix, "DECEL_STATE"), None)
    shared_controls.pop(prefixed(prefix, "HOLD_SECONDS"), None)
    shared_controls.pop(prefixed(prefix, "RESUME_TIME"), None)
    shared_controls.pop(prefixed(prefix, "ACTIVE"), None)
    shared_controls.pop(prefixed(prefix, "ACCEL_STATE"), None)


__all__ = [
    "record_requested_speed",
    "start_deceleration",
    "apply_deceleration",
    "start_acceleration",
    "apply_acceleration",
    "clear_stop_state",
]

