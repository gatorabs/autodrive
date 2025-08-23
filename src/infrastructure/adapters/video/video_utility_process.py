import io
import os
import glob
import contextlib
from typing import Union

import cv2 as cv
import numpy as np
from PIL import Image
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.services.lane_detection_service import (
    get_warp_points_from_controls,
    bird_eye_full,
)
from src.infrastructure.logging.logger import Logger

logger = Logger("FLAGS", verbose=True)

def toggle_named_window(is_enabled: bool, window_name: str, frame=None):
    if is_enabled and frame is not None:
        cv.imshow(window_name, frame)
    else:
        try:
            if cv.getWindowProperty(window_name, cv.WND_PROP_VISIBLE) >= 1:
                cv.destroyWindow(window_name)
        except cv.error:
            pass

def encode_frame(frame: Union[np.ndarray, bytes, bytearray]) -> bytes:
    if isinstance(frame, (bytes, bytearray)):
        return bytes(frame)
    if isinstance(frame, np.ndarray):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue()
    raise TypeError("Frame must be a numpy array or bytes")

def generate_placeholder_image():
    img = np.zeros((270, 480, 3), dtype=np.uint8)
    cv.putText(img, "Carregando Detector...", (50, 135),
                cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return encode_frame(img)


def detect_camera_indices(max_tested=3, exclude_indices=None):
    exclude_set = {str(i) for i in (exclude_indices or [])}
    available = []

    for i in range(max_tested + len(exclude_set)):
        if str(i) in exclude_set:
            continue
        with open(os.devnull, "w") as fnull, contextlib.redirect_stderr(fnull):
            cap = cv.VideoCapture(i)
            if cap is not None and cap.read()[0]:
                available.append(str(i))
            cap.release()

    qtd = len(available)
    if qtd == 0:
        logger.error("Nenhuma câmera foi detectada.")
    elif qtd == 1:
        logger.info(f"Câmera detectada: (índice {available[0]}).")
    else:
        logger.info(f"Câmeras detectadas: (índices {', '.join(available)})")
    return available


def get_video_files_from_folder(folder="resources/test_videos"):
    video_exts = ("*.mp4", "*.avi", "*.mov", "*.mkv")
    files = []
    for ext in video_exts:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(files)


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

def switch_video_source(video_processor, current_source, new_source, logger):
    if new_source != current_source:
        logger.info(f"Trocando Source de {current_source} para {new_source}")
        try:
            new_video = VideoProcessor(video_source=new_source)
        except Exception as e:
            logger.error(f"Falha ao trocar para fonte {new_source}: {e}")
            return video_processor, current_source
        if video_processor:
            video_processor.release()
        return new_video, new_source
    return video_processor, current_source


def open_video_source(current_source, lane_queue, shared_controls, logger, safe_stop_cb):
    try:
        video_proc = VideoProcessor(video_source=current_source)
        logger.info(f"Fonte aberta: {current_source}")
        return video_proc
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Falha ao abrir fonte {current_source}: {e}")
        safe_stop_cb(lane_queue, shared_controls, logger, reason=str(e))
        return None
