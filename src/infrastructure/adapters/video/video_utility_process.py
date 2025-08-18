import io
from typing import Union

import cv2 as cv
import numpy as np
from PIL import Image
from src.infrastructure.adapters.video.video_process import VideoProcessor

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
