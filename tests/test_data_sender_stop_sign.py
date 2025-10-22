import sys
import types
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

if "cv2" not in sys.modules:
    sys.modules["cv2"] = types.SimpleNamespace()

if "numpy" not in sys.modules:
    sys.modules["numpy"] = types.SimpleNamespace(mean=lambda data: 0)

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData
from src.infrastructure.services.data_sender_service import (
    STOP_SIGN_ACCELERATING,
    STOP_SIGN_DECELERATING,
    STOP_SIGN_HOLDING,
    STOP_SIGN_LABEL,
    publish_emergency_stop,
)


def _make_stop_object(label=STOP_SIGN_LABEL):
    return ObjectData(custom_object_label=label, traffic_light_data=2)


def test_stop_sign_flow_gradual_speed_changes():
    lane_data = LaneData(car_speed_data=150)
    obj_data = _make_stop_object()
    shared_controls = {}
    tk_controls = {"Timestamp": 5}

    now = 0.0

    # Initial detection should start a deceleration step.
    publish_emergency_stop(
        obj_data,
        shared_controls,
        lane_data,
        tk_controls,
        now=now,
    )

    assert shared_controls["STOP_SIGN_STATE"] == STOP_SIGN_DECELERATING
    assert lane_data.car_speed_data == 140
    assert shared_controls["STOP_SIGN_PREV_SPEED"] == 150

    zero_time = None

    # Continue decelerating until the car stops completely.
    for _ in range(20):
        now += 0.1
        publish_emergency_stop(
            obj_data,
            shared_controls,
            lane_data,
            tk_controls,
            now=now,
        )
        assert lane_data.car_speed_data % 10 == 0
        if lane_data.car_speed_data == 0:
            zero_time = now
            break

    assert zero_time is not None
    assert shared_controls["STOP_SIGN_STATE"] == STOP_SIGN_HOLDING

    resume_time = shared_controls["STOP_SIGN_RESUME_TIME"]
    assert abs(resume_time - (zero_time + 5.0)) < 1e-6

    # While holding, the car must remain stopped.
    hold_check_time = zero_time + 2.5
    publish_emergency_stop(
        obj_data,
        shared_controls,
        lane_data,
        tk_controls,
        now=hold_check_time,
    )
    assert shared_controls["STOP_SIGN_STATE"] == STOP_SIGN_HOLDING
    assert lane_data.car_speed_data == 0

    # When the hold time elapses, the state transitions to accelerating.
    publish_emergency_stop(
        obj_data,
        shared_controls,
        lane_data,
        tk_controls,
        now=resume_time,
    )
    assert shared_controls["STOP_SIGN_STATE"] == STOP_SIGN_ACCELERATING

    accelerated_speeds = []

    # Gradually return to the previous speed.
    while shared_controls.get("STOP_SIGN_ACTIVE", False):
        resume_time += 0.1
        publish_emergency_stop(
            obj_data,
            shared_controls,
            lane_data,
            tk_controls,
            now=resume_time,
        )
        accelerated_speeds.append(lane_data.car_speed_data)

    assert accelerated_speeds[0] == 10
    assert accelerated_speeds[-1] == 150
    assert all(
        later >= earlier for earlier, later in zip(accelerated_speeds, accelerated_speeds[1:])
    )
    assert not shared_controls.get("STOP_SIGN_ACTIVE", False)
    assert shared_controls.get("STOP_SIGN_IGNORE", False) is False
