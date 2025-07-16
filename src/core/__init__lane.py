import cv2 as cv
import time
import serial
from src.application.services.lane_detection_service import compute_distances, publish
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.adapters.video.video_preprocess import preprocess
from src.infrastructure.adapters.video.video_utility_process import toggle_named_window, switch_video_source
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.adapters.interface.setup_embedded_ui import draw_overlays
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.utils.update_time_processor import update_processing_time
from src.infrastructure.logging.logger import Logger
from src.domain.services.pid.pid_service import update_pid_from_controls, pid_setup, check_and_update_pid
from src.infrastructure.constants.usecases_constants.lane_process_constants import KP,KD,KI,MIN_OUTPUT,MAX_OUTPUT,TARGET_CENTER_DISTANCE
from src.infrastructure.mappers.direction_mapper import map_direction