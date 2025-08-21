import cv2 as cv
import time
import serial
import math

from src.infrastructure.services.lane_detection_service import (
    compute_distances,
    publish,
    compute_speed_and_direction,
    force_safe_stop,
    capture_frame_with_reopen,
)
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.adapters.video.video_preprocess import preprocess
from src.infrastructure.adapters.video.video_utility_process import (
    toggle_named_window,
    switch_video_source,
    open_video_source,
)
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.adapters.display.setup_embedded_ui import draw_overlays
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.utils.update_time_processor import update_processing_time
from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.pid_service import (
    update_pid_from_controls,
    pid_setup,
    check_and_update_pid,
)
from src.domain.constants.pid_constants import (
    KP,
    KD,
    KI,
    MIN_OUTPUT,
    MAX_OUTPUT,
    TARGET_CENTER_DISTANCE,
)
from src.infrastructure.mappers.direction_mapper import map_direction