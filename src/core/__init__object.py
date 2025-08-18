import time
from src.infrastructure.adapters.detection.object_detection import ObjectDetector
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.logging.logger import Logger
from src.infrastructure.constants.video_constants import FRAME_HEIGHT, FRAME_WIDTH
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.adapters.video.video_utility_process import (
    switch_video_source,
    open_video_source,
)
from src.infrastructure.services.object_detection_service import (
    capture_frame_with_reopen,
    force_default_object_data,
)
