import cv2 as cv
import time
import serial
from src.domain.services.pid_controller import PIDController
from src.domain.services.pid_v2_controller import PIDV2Controller
from src.domain.services.lane_distance_service import compute_distances
from src.infrastructure.adapters.video.video_processor import VideoProcessor
from src.infrastructure.adapters.video.preprocess import preprocess
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.adapters.interface.display import draw_overlays
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.utils.update_time_processor import update_processing_time
from src.infrastructure.logging.logger import Logger
from src.application.usecases.publishers.image_publisher import publish
from src.application.services.pid_service import update_pid_from_controls
from src.application.state.lane_process_state import LaneDetectionState
