from __future__ import annotations

from typing import NamedTuple


class Range(NamedTuple):
    min_value: float
    max_value: float
    step: float = 1.0


# Camera frame the perspective-warp points are defined against.
CAMERA_FRAME_WIDTH = 640
CAMERA_FRAME_HEIGHT = 480

WARP_X_RANGE = Range(0, CAMERA_FRAME_WIDTH)
WARP_Y_RANGE = Range(0, CAMERA_FRAME_HEIGHT)

# Image filters (OpenCV Canny edge-detection thresholds).
CANNY_RANGE = Range(0, 255)

# PID control gains.
KP_RANGE = Range(0.0, 5.0, 0.01)
KI_RANGE = Range(0.0, 10.0, 0.001)
KD_RANGE = Range(0.0, 10.0, 0.001)

# Lane-following operation values.
LINES_RANGE = Range(0, CAMERA_FRAME_HEIGHT)
DISTANCE_RANGE = Range(0, 270)
SPEED_RANGE = Range(0, 255)
SIDE_RANGE = Range(1, 2)

# Object detection thresholds.
PERSON_RANGE = Range(0, 240)
TRAFFIC_LIGHT_RANGE = Range(0, 240)
PEOPLE_REGION_RANGE = Range(10, 100)
SIGN_RANGE = Range(0, 240)

# Manual driving controls.
MANUAL_DIRECTION_RANGE = Range(0, 180)
MANUAL_SPEED_RANGE = Range(0, 255)

# YOLO confidence thresholds (tenths of a unit, i.e. 0-10 maps to 0.0-1.0).
CONFIDENCE_RANGE = Range(0, 10)
TIMESTAMP_RANGE = Range(0, 10)

# Stop-ramp behavior.
STOP_DECELERATION_STEP_RANGE = Range(1, 100)
STOP_RAMP_INTERVAL_RANGE = Range(0.0, 1.0, 0.05)
DEVIATION_COUNTER_RANGE = Range(0, 5)

__all__ = [
    "Range",
    "CAMERA_FRAME_WIDTH",
    "CAMERA_FRAME_HEIGHT",
    "WARP_X_RANGE",
    "WARP_Y_RANGE",
    "CANNY_RANGE",
    "KP_RANGE",
    "KI_RANGE",
    "KD_RANGE",
    "LINES_RANGE",
    "DISTANCE_RANGE",
    "SPEED_RANGE",
    "SIDE_RANGE",
    "PERSON_RANGE",
    "TRAFFIC_LIGHT_RANGE",
    "PEOPLE_REGION_RANGE",
    "SIGN_RANGE",
    "MANUAL_DIRECTION_RANGE",
    "MANUAL_SPEED_RANGE",
    "CONFIDENCE_RANGE",
    "TIMESTAMP_RANGE",
    "STOP_DECELERATION_STEP_RANGE",
    "STOP_RAMP_INTERVAL_RANGE",
    "DEVIATION_COUNTER_RANGE",
]
