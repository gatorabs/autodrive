import cv2 as cv
import time
import serial
from src.domain.services.pid_controller import PIDController
from src.domain.services.pid_v2_controller import PIDV2Controller
from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance
from src.infrastructure.adapters.video.video_processor import VideoProcessor
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.utils.warp_perspective_processor import bird_eye_full, get_warp_points_from_controls
from src.infrastructure.adapters.interface.display import draw_overlays

from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.utils.update_time_processor import update_processing_time
from src.infrastructure.logging.logger import Logger