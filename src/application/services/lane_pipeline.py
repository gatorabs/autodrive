from concurrent.futures import ThreadPoolExecutor
import math

import cv2 as cv

from src.domain.constants.pid_constants import FALLBACK_PID_INPUT, FALLBACK_PID_OUTPUT
from src.domain.services.detour_service import reset_detour_mode
from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance
from src.infrastructure.mappers.direction_mapper import map_direction
from src.infrastructure.media.frame_codec import encode_frame
from src.infrastructure.vision.perspective_transform import (
    bird_eye_full,
    get_warp_points_from_controls,
)

_encoder_pool = ThreadPoolExecutor(max_workers=2)


def preprocess(frame, tk_controls, morph_kernel):
    canny_1 = tk_controls.get("F_Canny")
    canny_2 = tk_controls.get("S_Canny")
    side = tk_controls.get("Side", 1)
    num_lines = tk_controls.get("Lines", 10)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (5, 5), 0)
    edges = cv.Canny(blur, canny_1, canny_2)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

    warp_points = get_warp_points_from_controls(tk_controls)
    warped_roi, max_height, _ = bird_eye_full(edges, warp_points, draw_on=frame)

    return edges, warp_points, warped_roi, side, num_lines, max_height


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

        shared_frames.publish_lane_frames(
            future_display.result(),
            future_edges.result(),
        )
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls.set_max_height(max_height)
    shared_controls.car_info = lane_data
    shared_controls.set_time_info(fps, avg_time)

def compute_distances(warped_roi, side, num_lines):
    if num_lines <= 0:
        interval = 1
    else:
        interval = max(1, round(warped_roi.shape[0] / num_lines))

    avg_left, avg_right, left_lines, right_lines = calculate_center_distance(
        warped_roi, interval)

    lost_ref = ((side == 1 and avg_right == float('inf')) or
                (side == 2 and avg_left == float('inf')))
    has_ref = not lost_ref

    return avg_left, avg_right, has_ref, left_lines, right_lines

def compute_speed_and_direction(pid,
                                avg_left,
                                avg_right,
                                side,
                                has_ref,
                                tk_controls,
                                direction,
                                shared_controls=None):

    def _lane_value(selected_side):
        return avg_right if selected_side == 1 else avg_left

    def _swap_side(selected_side):
        return 2 if selected_side == 1 else 1

    speed = tk_controls.get("Speed")
    lane_val = _lane_value(side)

    if (not has_ref) or (not math.isfinite(lane_val)):
        pid.fallback(FALLBACK_PID_INPUT)

        previous_side = side
        side = _swap_side(side)
        tk_controls["Side"] = side
        _restore_detour_settings_if_needed(shared_controls, tk_controls, previous_side, side)
        lane_val = _lane_value(side)

        if not math.isfinite(lane_val):
            return 0, direction, side

    # Calcula a direção com o novo valor de lane_val
    raw_direction = pid.calculate(lane_val)

    if raw_direction is None or not math.isfinite(raw_direction):
        pid.fallback(FALLBACK_PID_OUTPUT)
        return speed, direction, side
    return speed, round(raw_direction), side

def force_safe_stop(lane_queue, shared_controls, logger, reason="CAMERA_ERROR"):

    shared_controls["CAR_SPEED_DATA"] = 0
    direction = shared_controls.car_info.get("CAR_DIRECTION_DATA", 90)

    lane_data = {
        "CAR_SPEED_DATA": 0,
        "CAR_DIRECTION_DATA": direction
    }

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls.safe_stop = True
    logger.warning(f"SAFE-STOP ativado ({reason}).")


def try_capture_or_mark_for_reopen(video_proc,
                              current_source,
                              lane_queue,
                              shared_controls,
                              logger):
    try:
        frame = video_proc.get_frame()
        shared_controls.safe_stop = False
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

def apply_speed_override(
    shared_controls,
    tk_controls,
    current_speed,
    key="SPEED_OVERRIDE",
    tk_key="Speed",
    min_val=0,
    max_val=255,
):

    override = shared_controls.get(key)

    if override is None:
        return current_speed
    if isinstance(override, float) and math.isnan(override):
        return current_speed

    if not isinstance(override, (int, float)):
        return current_speed

    normalized = int(round(override))
    normalized = max(min_val, min(normalized, max_val))

    if tk_controls.get(tk_key) != normalized:
        tk_controls[tk_key] = normalized

    return normalized


def _restore_detour_settings_if_needed(shared_controls, tk_controls, previous_side, new_side):
    if previous_side != 1 or new_side != 2:
        return
    reset_detour_mode(shared_controls, tk_controls)
