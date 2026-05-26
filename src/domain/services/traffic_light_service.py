"""Service handling traffic light interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.utils import clamp_speed, prefixed

from . import ramp_service

TRAFFIC_LIGHT_PREFIX = "TRAFFIC_LIGHT"
TRAFFIC_LIGHT_CONTROL_PREFIX = "SEMAFORO"
TRAFFIC_LIGHT_PREV_SPEED_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "PREV_SPEED")
TRAFFIC_LIGHT_LAST_STATE_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "LAST_STATE")
TRAFFIC_LIGHT_STOP_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "STOP_ACTIVE")
TRAFFIC_LIGHT_YELLOW_TARGET_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "YELLOW_TARGET")
TRAFFIC_LIGHT_DECEL_STATE_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "DECEL_STATE")
TRAFFIC_LIGHT_LAST_SPEED_KEY = prefixed(TRAFFIC_LIGHT_PREFIX, "LAST_SPEED")

TRAFFIC_LIGHT_RED = 0
TRAFFIC_LIGHT_YELLOW = 1
TRAFFIC_LIGHT_GREEN = 2
TRAFFIC_LIGHT_SPEED_OFFSET = 30


@dataclass
class TrafficLightEvaluation:
    should_stop: bool
    target_speed: Optional[int]


def evaluate_state(
    shared_controls: dict,
    lane_data,
    traffic_light_state: Any,
) -> TrafficLightEvaluation:
    if shared_controls is None or lane_data is None:
        return TrafficLightEvaluation(False, None)

    try:
        state = int(traffic_light_state)
    except (TypeError, ValueError):
        state = TRAFFIC_LIGHT_GREEN

    last_state = shared_controls.get(TRAFFIC_LIGHT_LAST_STATE_KEY)

    stop_required = False
    target_speed: Optional[int] = None

    if state == TRAFFIC_LIGHT_RED:
        if TRAFFIC_LIGHT_PREV_SPEED_KEY not in shared_controls:
            shared_controls[TRAFFIC_LIGHT_PREV_SPEED_KEY] = clamp_speed(
                getattr(lane_data, "car_speed_data", 0)
            )
        shared_controls[TRAFFIC_LIGHT_STOP_KEY] = True
        shared_controls.pop(TRAFFIC_LIGHT_YELLOW_TARGET_KEY, None)
        stop_required = True
        target_speed = 0
    elif state == TRAFFIC_LIGHT_YELLOW:
        if shared_controls.get(TRAFFIC_LIGHT_STOP_KEY):
            stop_required = True
            target_speed = 0
        else:
            if last_state != TRAFFIC_LIGHT_YELLOW:
                shared_controls[TRAFFIC_LIGHT_PREV_SPEED_KEY] = clamp_speed(
                    getattr(lane_data, "car_speed_data", 0)
                )
                base_speed = shared_controls[TRAFFIC_LIGHT_PREV_SPEED_KEY]
                target_speed = max(0, base_speed - TRAFFIC_LIGHT_SPEED_OFFSET)
                shared_controls[TRAFFIC_LIGHT_YELLOW_TARGET_KEY] = target_speed
            else:
                base_speed = shared_controls.get(TRAFFIC_LIGHT_PREV_SPEED_KEY)
                if base_speed is None:
                    base_speed = clamp_speed(getattr(lane_data, "car_speed_data", 0))
                    shared_controls[TRAFFIC_LIGHT_PREV_SPEED_KEY] = base_speed
                target_speed = shared_controls.get(TRAFFIC_LIGHT_YELLOW_TARGET_KEY)
                if target_speed is None:
                    target_speed = max(0, base_speed - TRAFFIC_LIGHT_SPEED_OFFSET)
                    shared_controls[TRAFFIC_LIGHT_YELLOW_TARGET_KEY] = target_speed
            if target_speed is not None:
                target_speed = clamp_speed(target_speed)
    elif state == TRAFFIC_LIGHT_GREEN:
        was_stop = bool(shared_controls.pop(TRAFFIC_LIGHT_STOP_KEY, False))
        base_speed = shared_controls.pop(TRAFFIC_LIGHT_PREV_SPEED_KEY, None)
        shared_controls.pop(TRAFFIC_LIGHT_YELLOW_TARGET_KEY, None)
        shared_controls.pop(TRAFFIC_LIGHT_DECEL_STATE_KEY, None)

        if base_speed is not None:
            base_speed = clamp_speed(base_speed)
        if was_stop or last_state == TRAFFIC_LIGHT_YELLOW:
            if base_speed is not None:
                target_speed = base_speed
        stop_required = False
    else:
        if shared_controls.get(TRAFFIC_LIGHT_STOP_KEY):
            stop_required = True
            target_speed = 0

    shared_controls[TRAFFIC_LIGHT_LAST_STATE_KEY] = state
    return TrafficLightEvaluation(stop_required, target_speed)


def start_deceleration(
    shared_controls: dict,
    initial_speed: Any,
    tk_controls: Any,
    current_time: float,
) -> None:
    ramp_service.start_deceleration(
        shared_controls,
        initial_speed,
        tk_controls,
        current_time,
        prefix=TRAFFIC_LIGHT_PREFIX,
        control_key_prefix=TRAFFIC_LIGHT_CONTROL_PREFIX,
    )


def apply_deceleration(
    shared_controls: dict, tk_controls: Any, current_time: float
) -> Optional[int]:
    if not shared_controls.get(TRAFFIC_LIGHT_DECEL_STATE_KEY):
        return None

    return ramp_service.apply_deceleration(
        shared_controls,
        tk_controls,
        current_time,
        prefix=TRAFFIC_LIGHT_PREFIX,
        control_key_prefix=TRAFFIC_LIGHT_CONTROL_PREFIX,
    )


def prepare_acceleration(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    current_time: float,
    desired_speed: Optional[int],
) -> None:
    if desired_speed is None:
        if not shared_controls.get(TRAFFIC_LIGHT_STOP_KEY):
            shared_controls.pop(TRAFFIC_LIGHT_PREV_SPEED_KEY, None)
        return

    desired = clamp_speed(desired_speed)
    if desired <= 0:
        shared_controls.pop(prefixed(TRAFFIC_LIGHT_PREFIX, "ACCEL_STATE"), None)
        shared_controls.pop(TRAFFIC_LIGHT_PREV_SPEED_KEY, None)
        return

    shared_controls[TRAFFIC_LIGHT_PREV_SPEED_KEY] = desired
    if not shared_controls.get(prefixed(TRAFFIC_LIGHT_PREFIX, "ACCEL_STATE")):
        ramp_service.start_acceleration(
            shared_controls,
            getattr(lane_data, "car_speed_data", 0),
            desired,
            tk_controls,
            current_time,
            prefix=TRAFFIC_LIGHT_PREFIX,
            control_key_prefix=TRAFFIC_LIGHT_CONTROL_PREFIX,
        )


def apply_acceleration(
    shared_controls: dict,
    tk_controls: Any,
    current_time: float,
) -> Optional[int]:
    result = ramp_service.apply_acceleration(
        shared_controls,
        tk_controls,
        current_time,
        prefix=TRAFFIC_LIGHT_PREFIX,
        control_key_prefix=TRAFFIC_LIGHT_CONTROL_PREFIX,
    )
    if result is None:
        return None

    speed, finished = result
    if finished:
        shared_controls.pop(TRAFFIC_LIGHT_PREV_SPEED_KEY, None)
        ramp_service.clear_stop_state(shared_controls, prefix=TRAFFIC_LIGHT_PREFIX)
    return speed


__all__ = [
    "TRAFFIC_LIGHT_PREFIX",
    "TRAFFIC_LIGHT_CONTROL_PREFIX",
    "TRAFFIC_LIGHT_PREV_SPEED_KEY",
    "TRAFFIC_LIGHT_LAST_STATE_KEY",
    "TRAFFIC_LIGHT_STOP_KEY",
    "TRAFFIC_LIGHT_YELLOW_TARGET_KEY",
    "TRAFFIC_LIGHT_DECEL_STATE_KEY",
    "TRAFFIC_LIGHT_LAST_SPEED_KEY",
    "TRAFFIC_LIGHT_RED",
    "TRAFFIC_LIGHT_YELLOW",
    "TRAFFIC_LIGHT_GREEN",
    "TrafficLightEvaluation",
    "evaluate_state",
    "start_deceleration",
    "apply_deceleration",
    "prepare_acceleration",
    "apply_acceleration",
]
