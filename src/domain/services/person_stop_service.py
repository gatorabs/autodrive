"""Service dealing with emergency stops triggered by pedestrians."""
from __future__ import annotations

from typing import Any, Optional

from src.domain.utils import clamp_speed, prefixed

from . import ramp_service

PERSON_PREFIX = "PERSON"


def prepare_stop(shared_controls: dict, lane_data, person_detected: bool) -> None:
    if not person_detected:
        return

    if shared_controls.get(prefixed(PERSON_PREFIX, "PREV_SPEED")) is None:
        ramp_service.record_requested_speed(
            shared_controls, lane_data, prefix=PERSON_PREFIX
        )
        prev_speed = shared_controls.get(prefixed(PERSON_PREFIX, "PREV_SPEED"))
        if prev_speed is None:
            fallback_speed = (
                shared_controls.get(prefixed(PERSON_PREFIX, "LAST_SPEED"))
                or shared_controls.get("STOP_SIGN_LAST_SPEED")
            )
            inferred = clamp_speed(fallback_speed)
            if inferred > 0:
                shared_controls[prefixed(PERSON_PREFIX, "PREV_SPEED")] = inferred
    shared_controls[prefixed(PERSON_PREFIX, "STOP_ACTIVE")] = True


def handle_resume(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    current_time: float,
    person_detected: bool,
) -> Optional[int]:
    prev_speed = shared_controls.get(prefixed(PERSON_PREFIX, "PREV_SPEED"))
    override_speed: Optional[int] = None
    override_raw = shared_controls.get("SPEED_OVERRIDE")
    if isinstance(override_raw, (int, float)):
        override_speed = clamp_speed(override_raw)

    if (
        prev_speed is not None
        and shared_controls.get(prefixed(PERSON_PREFIX, "STOP_ACTIVE"), False)
        and not person_detected
    ):
        if override_speed is not None and override_speed <= 0:
            shared_controls.pop(prefixed(PERSON_PREFIX, "PREV_SPEED"), None)
            shared_controls[prefixed(PERSON_PREFIX, "STOP_ACTIVE")] = False
            ramp_service.clear_stop_state(shared_controls, prefix=PERSON_PREFIX)
            return 0

        if not shared_controls.get(prefixed(PERSON_PREFIX, "ACCEL_STATE")):
            ramp_service.start_acceleration(
                shared_controls,
                getattr(lane_data, "car_speed_data", 0),
                prev_speed,
                tk_controls,
                current_time,
                prefix=PERSON_PREFIX,
            )

        result = ramp_service.apply_acceleration(
            shared_controls,
            tk_controls,
            current_time,
            prefix=PERSON_PREFIX,
        )
        if result is not None:
            speed, finished = result
            if finished:
                shared_controls.pop(prefixed(PERSON_PREFIX, "PREV_SPEED"), None)
                shared_controls[prefixed(PERSON_PREFIX, "STOP_ACTIVE")] = False
                ramp_service.clear_stop_state(shared_controls, prefix=PERSON_PREFIX)
            return speed

        fallback_speed = clamp_speed(prev_speed)
        shared_controls.pop(prefixed(PERSON_PREFIX, "PREV_SPEED"), None)
        shared_controls[prefixed(PERSON_PREFIX, "STOP_ACTIVE")] = False
        ramp_service.clear_stop_state(shared_controls, prefix=PERSON_PREFIX)
        return fallback_speed

    if not person_detected:
        shared_controls.pop(prefixed(PERSON_PREFIX, "PREV_SPEED"), None)
        shared_controls.pop(prefixed(PERSON_PREFIX, "STOP_ACTIVE"), None)
        ramp_service.clear_stop_state(shared_controls, prefix=PERSON_PREFIX)

    return None


__all__ = [
    "PERSON_PREFIX",
    "prepare_stop",
    "handle_resume",
]
