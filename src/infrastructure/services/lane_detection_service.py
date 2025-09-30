import math

from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance
import cv2 as cv
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.mappers.direction_mapper import map_direction
from src.infrastructure.utils.frame_utils import encode_frame
from src.domain.constants.pid_constants import FALLBACK_PID_INPUT, FALLBACK_PID_OUTPUT

_encoder_pool = ThreadPoolExecutor(max_workers=2)

def publish(frame_display,
            edges,
            lane_queue,
            shared_frames,
            shared_controls,
            lane_data,
            fps,
            avg_time,
            max_height,
            logger):
    """
    Codifica quadros de exibição em paralelo usando a função de encode genérica,
    envia comandos de direção para a fila e atualiza a memória compartilhada com
    bytes de quadro e telemetria.
    """
    try:
        future_display = _encoder_pool.submit(encode_frame, frame_display)
        future_edges   = _encoder_pool.submit(encode_frame, edges)

        shared_frames["NORMAL_FRAME"] = future_display.result()
        shared_frames["EDGES_FRAME"]  = future_edges.result()
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls["MAX_HEIGHT"] = max_height
    shared_controls["CAR_INFO"]  = lane_data
    shared_controls["TIME_INFO"] = {
        'fps': round(fps, 0),
        'total_processing_time': round(avg_time, 2)
    }

def compute_distances(warped_roi, side, num_lines):
    if num_lines <= 0:
        interval = 1
    else:
        interval = max(1, round(warped_roi.shape[0] / num_lines))

    avg_left, avg_right, left_lines, right_lines = calculate_center_distance(
        warped_roi, interval)

    lost_ref = ((side == 1 and avg_right == float('inf')) or
                (side == 0 and avg_left == float('inf')))
    has_ref = not lost_ref

    return avg_left, avg_right, has_ref, left_lines, right_lines

def compute_speed_and_direction(pid,
                                avg_left,
                                avg_right,
                                side,
                                has_ref,
                                tk_controls,
                                direction):

    if not has_ref:
        return 0, direction

    speed = tk_controls.get("Speed")
    lane_val = avg_right if side == 1 else avg_left

    if not math.isfinite(lane_val):
        pid.fallback(FALLBACK_PID_INPUT)

        side = 0 if side == 1 else 1
        lane_val = avg_right if side == 1 else avg_left

        if not math.isfinite(lane_val):
            return speed, direction

    # Calcula a direção com o novo valor de lane_val
    raw_direction = pid.calculate(lane_val)

    if raw_direction is None or not math.isfinite(raw_direction):
        pid.fallback(FALLBACK_PID_OUTPUT)
        return speed, direction

    return speed, round(raw_direction)

def force_safe_stop(lane_queue, shared_controls, logger, reason="CAMERA_ERROR"):

    shared_controls["CAR_SPEED_DATA"] = 0
    direction = shared_controls.get("CAR_INFO", {}).get("CAR_DIRECTION_DATA", 90)

    lane_data = {
        "CAR_SPEED_DATA": 0,
        "CAR_DIRECTION_DATA": direction
    }

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls["SAFE_STOP"] = True
    logger.warning(f"SAFE-STOP ativado ({reason}).")


def try_capture_or_mark_for_reopen(video_proc,
                              current_source,
                              lane_queue,
                              shared_controls,
                              logger):
    try:
        frame = video_proc.get_frame()
        shared_controls["SAFE_STOP"] = False
        return video_proc, frame
    except RuntimeError as e:
        force_safe_stop(lane_queue, shared_controls, logger, reason=str(e))
        try:
            video_proc.release()
        except Exception:
            pass
        return None, None

def define_and_calculate_side(direction, side):
    if side == 1:
        mapped_direction = map_direction(value=direction, out_min=180, out_max=0)
        return mapped_direction
    else:
        mapped_direction = map_direction(value=direction)
        return mapped_direction
