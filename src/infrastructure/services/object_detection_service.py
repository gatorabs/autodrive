import cv2
import numpy as np
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT

def process_traffic_light_roi(roi):
    active_color = "Unknown"
    color_bgr = (255, 255, 255)  # branco padrão
    traffic_light_state = 2  # padrão: verde

    if roi.size != 0:
        # 1) converte para gray e dá um leve blur para reduzir ruído
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2) dimensões
        h = gray.shape[0]
        h_third = h // 3

        # 3) extrai as 3 regiões
        red_roi = gray[0:h_third, :]
        yellow_roi = gray[h_third:2 * h_third, :]
        green_roi = gray[2 * h_third:h, :]

        # 4) calcula a média de intensidade em cada região
        mean_red = np.mean(red_roi)
        mean_yellow = np.mean(yellow_roi)
        mean_green = np.mean(green_roi)

        means = {
            "Red": mean_red,
            "Yellow": mean_yellow,
            "Green": mean_green
        }

        active_color = max(means, key=means.get)

        # 5) mapeia o resultado para BGR e estado
        if active_color == "Red":
            color_bgr = (0, 0, 255)
            traffic_light_state = 0
        elif active_color == "Yellow":
            color_bgr = (0, 255, 255)
            traffic_light_state = 1
        elif active_color == "Green":
            color_bgr = (0, 255, 0)
            traffic_light_state = 2

    return active_color, color_bgr, traffic_light_state

def publish_results(
    shared_serial_data,
    shared_frames,
    person_detected,
    traffic_light_state,
    object_queue,
    frame,
    custom_detection_state=None,
):
    custom_detection_state = custom_detection_state or {}
    shared_serial_data[2] = 1 if person_detected else 0
    shared_serial_data[1] = traffic_light_state
    custom_serial_value = 1 if custom_detection_state.get("any") else 0
    if len(shared_serial_data) > 0:
        shared_serial_data[0] = custom_serial_value

    # mantém o frame bruto; consumidores decidem como codificar
    shared_frames["OBJECT_FRAME"] = frame.copy()

    object_data = {
        "OBJECT_PERSON_DATA": shared_serial_data[2],
        "TRAFFIC_LIGHT_DATA": shared_serial_data[1],
        "CUSTOM_OBJECT_DATA": (
            shared_serial_data[0] if len(shared_serial_data) > 0 else custom_serial_value
        ),
        "STOP_SIGN_DATA": 1 if custom_detection_state.get("stop_sign") else 0,
        "DETOUR_SIGN_DATA": 1 if custom_detection_state.get("detour_sign") else 0,
        "SPEED_BUMP_SIGN_DATA": 1 if custom_detection_state.get("speed_bump_sign") else 0,
    }
    if not object_queue.full():
        object_queue.put(object_data)

def force_default_object_data(object_queue, shared_serial_data, shared_controls, logger, reason="CAMERA_ERROR"):
    custom_serial_value = 0
    if len(shared_serial_data) > 0:
        shared_serial_data[0] = custom_serial_value
    shared_serial_data[1] = 2
    shared_serial_data[2] = 1

    object_data = {
        "OBJECT_PERSON_DATA": 1,
        "TRAFFIC_LIGHT_DATA": 2,
        "CUSTOM_OBJECT_DATA": (
            shared_serial_data[0] if len(shared_serial_data) > 0 else custom_serial_value
        ),
        "STOP_SIGN_DATA": 0,
        "DETOUR_SIGN_DATA": 0,
        "SPEED_BUMP_SIGN_DATA": 0,
    }
    if not object_queue.full():
        object_queue.put(object_data)

    shared_controls["OBJ_SAFE_STOP"] = True
    shared_controls["DETOUR_SIGN_DETECTED"] = False
    shared_controls["SPEED_BUMP_SIGN_DETECTED"] = False
    shared_controls["STOP_SIGN_STATE"] = {
        "active_until": 0.0,
        "awaiting_clear": False,
        "resumed": False,
        "restore_speed": None,
    }
    logger.warning(f"OBJ-SAFE-STOP ativado ({reason}).")

def try_capture_or_mark_for_reopen(video_proc,
                              current_source,
                              object_queue,
                              shared_controls,
                              shared_serial_data,
                              logger):
    try:
        frame = video_proc.get_frame()
        shared_controls["OBJ_SAFE_STOP"] = False
        return video_proc, frame
    except RuntimeError as e:
        force_default_object_data(object_queue, shared_serial_data, shared_controls, logger, reason=str(e))
        try:
            video_proc.release()
        except Exception:
            pass
        return None, None
