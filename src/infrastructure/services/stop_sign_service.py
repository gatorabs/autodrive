"""Service handling stop sign interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.infrastructure.utils import clamp_speed, prefixed
from src.infrastructure.utils import get_stop_hold_seconds

from . import ramp_service

STOP_SIGN_LABEL = "PLACA_PARE"
STOP_SIGN_PREFIX = "STOP_SIGN"


@dataclass
class StopPhaseResult:
    hold_active: bool
    has_deceleration: bool


def evaluate_stop_phase(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    custom_label: str,
    current_time: float,
) -> StopPhaseResult:
    hold = False

    if shared_controls.get(prefixed(STOP_SIGN_PREFIX, "ACTIVE"), False):
        resume_time = shared_controls.get(prefixed(STOP_SIGN_PREFIX, "RESUME_TIME"))
        if resume_time is not None and current_time >= resume_time:
            shared_controls[prefixed(STOP_SIGN_PREFIX, "ACTIVE")] = False
            shared_controls.pop(prefixed(STOP_SIGN_PREFIX, "RESUME_TIME"), None)
            shared_controls.pop(prefixed(STOP_SIGN_PREFIX, "HOLD_SECONDS"), None)
        else:
            hold = True
            ramp_service.record_requested_speed(shared_controls, lane_data)

    if (
        not shared_controls.get(prefixed(STOP_SIGN_PREFIX, "ACTIVE"), False)
        and custom_label == STOP_SIGN_LABEL
        and not shared_controls.get(prefixed(STOP_SIGN_PREFIX, "IGNORE"), False)
    ):
        hold_seconds = get_stop_hold_seconds(tk_controls)
        shared_controls[prefixed(STOP_SIGN_PREFIX, "ACTIVE")] = hold_seconds > 0
        shared_controls[prefixed(STOP_SIGN_PREFIX, "RESUME_TIME")] = None
        shared_controls[prefixed(STOP_SIGN_PREFIX, "HOLD_SECONDS")] = hold_seconds
        ramp_service.record_requested_speed(shared_controls, lane_data, force=True)
        shared_controls[prefixed(STOP_SIGN_PREFIX, "IGNORE")] = True
        ramp_service.start_deceleration(
            shared_controls,
            getattr(lane_data, "car_speed_data", 0),
            tk_controls,
            current_time,
        )
        hold = True

    if (
        custom_label != STOP_SIGN_LABEL
        and not shared_controls.get(prefixed(STOP_SIGN_PREFIX, "ACTIVE"), False)
    ):
        shared_controls[prefixed(STOP_SIGN_PREFIX, "IGNORE")] = False

    decel_state = shared_controls.get(prefixed(STOP_SIGN_PREFIX, "DECEL_STATE"))
    if decel_state:
        ramp_service.record_requested_speed(shared_controls, lane_data)
        current_speed = clamp_speed(decel_state.get("current_speed", 0))
        target_speed = clamp_speed(decel_state.get("target_speed", 0))
        if (
            current_speed > target_speed
            or shared_controls.get(prefixed(STOP_SIGN_PREFIX, "ACTIVE"), False)
        ):
            hold = True

    return StopPhaseResult(hold_active=hold, has_deceleration=bool(decel_state))


def apply_deceleration(shared_controls: dict, tk_controls: Any, current_time: float) -> int:
    return ramp_service.apply_deceleration(
        shared_controls, tk_controls, current_time, prefix=STOP_SIGN_PREFIX
    )


def handle_resume_phase(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    current_time: float,
) -> Optional[int]:
    shared_controls.pop(prefixed(STOP_SIGN_PREFIX, "DECEL_STATE"), None)
    prev_speed = shared_controls.get(prefixed(STOP_SIGN_PREFIX, "PREV_SPEED"))

    if prev_speed is not None:
        if not shared_controls.get(prefixed(STOP_SIGN_PREFIX, "ACCEL_STATE")):
            ramp_service.start_acceleration(
                shared_controls,
                getattr(lane_data, "car_speed_data", 0),
                prev_speed,
                tk_controls,
                current_time,
                prefix=STOP_SIGN_PREFIX,
            )

        result = ramp_service.apply_acceleration(
            shared_controls,
            tk_controls,
            current_time,
            prefix=STOP_SIGN_PREFIX,
        )
        if result is not None:
            speed, finished = result
            if finished:
                shared_controls.pop(prefixed(STOP_SIGN_PREFIX, "PREV_SPEED"), None)
                ramp_service.clear_stop_state(shared_controls, prefix=STOP_SIGN_PREFIX)
            return speed

        fallback_speed = clamp_speed(prev_speed)
        shared_controls.pop(prefixed(STOP_SIGN_PREFIX, "PREV_SPEED"), None)
        ramp_service.clear_stop_state(shared_controls, prefix=STOP_SIGN_PREFIX)
        return fallback_speed

    ramp_service.clear_stop_state(shared_controls, prefix=STOP_SIGN_PREFIX)
    return None


__all__ = [
    "STOP_SIGN_LABEL",
    "STOP_SIGN_PREFIX",
    "StopPhaseResult",
    "evaluate_stop_phase",
    "apply_deceleration",
    "handle_resume_phase",
]
