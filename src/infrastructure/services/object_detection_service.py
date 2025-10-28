import cv2
import numpy as np
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.utils.frame_utils import encode_frame


CUSTOM_OBJECT_PRIORITY = [
    ("PLACA_PARE", 1),
    ("PLACA_DESVIO", 2),
    ("PLACA_LOMBADA", 3),
]
CUSTOM_OBJECT_CODE_BY_LABEL = {label: code for label, code in CUSTOM_OBJECT_PRIORITY}
CUSTOM_OBJECT_LABEL_BY_CODE = {code: label for label, code in CUSTOM_OBJECT_PRIORITY}

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

        # Quando a bounding box fica muito baixa (semáforo distante ou ruído),
        # dividir em três regiões pode resultar em slices vazios. Nesse cenário
        # não há dados suficientes para classificar a cor do semáforo e as
        # médias produziriam NaN, forçando "Red" por padrão. Ao detectar essa
        # condição, retornamos o estado padrão (verde) e mantemos "Unknown".
        if h_third == 0:
            return active_color, color_bgr, traffic_light_state

        # 3) extrai as 3 regiões
        red_roi = gray[0:h_third, :]
        yellow_roi = gray[h_third:2 * h_third, :]
        green_roi = gray[2 * h_third:h, :]

        # 4) calcula a média de intensidade em cada região
        mean_red = np.nanmean(red_roi)
        mean_yellow = np.nanmean(yellow_roi)
        mean_green = np.nanmean(green_roi)

        means = {
            "Red": mean_red,
            "Yellow": mean_yellow,
            "Green": mean_green
        }

        if any(np.isnan(value) for value in means.values()):
            return active_color, color_bgr, traffic_light_state

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
    detected_custom_objects=None,
):
    shared_serial_data[2] = 1 if person_detected else 0
    shared_serial_data[1] = traffic_light_state

    if detected_custom_objects is None:
        detected_custom_objects = set()
    else:
        detected_custom_objects = set(detected_custom_objects)

    custom_label = ""
    custom_serial_value = 0
    for label, code in CUSTOM_OBJECT_PRIORITY:
        if label in detected_custom_objects:
            custom_label = label
            custom_serial_value = code
            break

    if len(shared_serial_data) > 0:
        shared_serial_data[0] = custom_serial_value

    # evite enviar arrays grandes via Manager: compartilhe apenas JPEG codificado
    if frame is not None:
        try:
            shared_frames["OBJECT_FRAME"] = encode_frame(frame)
        except Exception:
            shared_frames["OBJECT_FRAME"] = None
    else:
        shared_frames["OBJECT_FRAME"] = None

    object_data = {
        "OBJECT_PERSON_DATA": shared_serial_data[2],
        "TRAFFIC_LIGHT_DATA": shared_serial_data[1],
        "CUSTOM_OBJECT_DATA": (
            shared_serial_data[0] if len(shared_serial_data) > 0 else custom_serial_value
        ),
        "CUSTOM_OBJECT_LABEL": custom_label,
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
        "CUSTOM_OBJECT_LABEL": "",
    }
    if not object_queue.full():
        object_queue.put(object_data)

    shared_controls["OBJ_SAFE_STOP"] = True
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
