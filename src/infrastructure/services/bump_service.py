"""Service handling bump (speed bump) interactions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.utils import clamp_speed, prefixed
from src.utils.stop_control import get_stop_hold_seconds

from . import ramp_service
from .detour_service import reset_detour_mode

BUMP_LABEL = "PLACA_LOMBADA"
BUMP_PREFIX = "BUMP"


@dataclass
class BumpPhaseResult:
    hold_active: bool
    has_deceleration: bool


def evaluate_stop_phase(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    custom_label: str,
    current_time: float,
) -> BumpPhaseResult:
    hold = False

    if shared_controls.get(prefixed(BUMP_PREFIX, "ACTIVE"), False):
        resume_time = shared_controls.get(prefixed(BUMP_PREFIX, "RESUME_TIME"))
        if resume_time is not None and current_time >= resume_time:
            shared_controls[prefixed(BUMP_PREFIX, "ACTIVE")] = False
            shared_controls.pop(prefixed(BUMP_PREFIX, "RESUME_TIME"), None)
            shared_controls.pop(prefixed(BUMP_PREFIX, "HOLD_SECONDS"), None)
        else:
            hold = True
            ramp_service.record_requested_speed(
                shared_controls, lane_data, prefix=BUMP_PREFIX
            )

    if (
        not shared_controls.get(prefixed(BUMP_PREFIX, "ACTIVE"), False)
        and custom_label == BUMP_LABEL
        and not shared_controls.get(prefixed(BUMP_PREFIX, "IGNORE"), False)
    ):
        reset_detour_mode(shared_controls, tk_controls)
        hold_seconds = get_stop_hold_seconds(tk_controls)
        shared_controls[prefixed(BUMP_PREFIX, "ACTIVE")] = hold_seconds > 0
        shared_controls[prefixed(BUMP_PREFIX, "RESUME_TIME")] = None
        shared_controls[prefixed(BUMP_PREFIX, "HOLD_SECONDS")] = hold_seconds
        ramp_service.record_requested_speed(
            shared_controls, lane_data, force=True, prefix=BUMP_PREFIX
        )
        shared_controls[prefixed(BUMP_PREFIX, "IGNORE")] = True
        starting_speed = clamp_speed(getattr(lane_data, "car_speed_data", 0))
        target_speed = max(0, starting_speed // 2)
        ramp_service.start_deceleration(
            shared_controls,
            getattr(lane_data, "car_speed_data", 0),
            tk_controls,
            current_time,
            prefix=BUMP_PREFIX,
            target_speed=target_speed,
        )
        hold = True

    if (
        custom_label != BUMP_LABEL
        and not shared_controls.get(prefixed(BUMP_PREFIX, "ACTIVE"), False)
    ):
        shared_controls[prefixed(BUMP_PREFIX, "IGNORE")] = False

    decel_state = shared_controls.get(prefixed(BUMP_PREFIX, "DECEL_STATE"))
    if decel_state:
        ramp_service.record_requested_speed(
            shared_controls, lane_data, prefix=BUMP_PREFIX
        )
        current_speed = clamp_speed(decel_state.get("current_speed", 0))
        target_speed = clamp_speed(decel_state.get("target_speed", 0))
        if (
            current_speed > target_speed
            or shared_controls.get(prefixed(BUMP_PREFIX, "ACTIVE"), False)
        ):
            hold = True

    return BumpPhaseResult(hold_active=hold, has_deceleration=bool(decel_state))


def apply_deceleration(shared_controls: dict, tk_controls: Any, current_time: float) -> int:
    return ramp_service.apply_deceleration(
        shared_controls, tk_controls, current_time, prefix=BUMP_PREFIX
    )


def handle_resume_phase(
    shared_controls: dict,
    lane_data,
    tk_controls: Any,
    current_time: float,
) -> Optional[int]:
    shared_controls.pop(prefixed(BUMP_PREFIX, "DECEL_STATE"), None)
    prev_speed = shared_controls.get(prefixed(BUMP_PREFIX, "PREV_SPEED"))

    if prev_speed is not None:
        if not shared_controls.get(prefixed(BUMP_PREFIX, "ACCEL_STATE")):
            ramp_service.start_acceleration(
                shared_controls,
                getattr(lane_data, "car_speed_data", 0),
                prev_speed,
                tk_controls,
                current_time,
                prefix=BUMP_PREFIX,
            )

        result = ramp_service.apply_acceleration(
            shared_controls,
            tk_controls,
            current_time,
            prefix=BUMP_PREFIX,
        )
        if result is not None:
            speed, finished = result
            if finished:
                shared_controls.pop(prefixed(BUMP_PREFIX, "PREV_SPEED"), None)
                ramp_service.clear_stop_state(shared_controls, prefix=BUMP_PREFIX)
            return speed

        fallback_speed = clamp_speed(prev_speed)
        shared_controls.pop(prefixed(BUMP_PREFIX, "PREV_SPEED"), None)
        ramp_service.clear_stop_state(shared_controls, prefix=BUMP_PREFIX)
        return fallback_speed

    ramp_service.clear_stop_state(shared_controls, prefix=BUMP_PREFIX)
    return None


__all__ = [
    "BUMP_LABEL",
    "BUMP_PREFIX",
    "BumpPhaseResult",
    "evaluate_stop_phase",
    "apply_deceleration",
    "handle_resume_phase",
]
