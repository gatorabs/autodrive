import cv2 as cv
import numpy as np
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

def generate_placeholder_image():
    img = np.zeros((270, 480, 3), dtype=np.uint8)
    cv.putText(img, "Carregando Detector...", (50, 135),
                cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    ret, jpeg = cv.imencode('.jpg', img)
    return jpeg.tobytes()

def switch_video_source(video_processor, current_source, new_source, logger):
    if new_source != current_source:
        logger.info(f"Trocando Source de {current_source} para {new_source}")
        if video_processor:
            video_processor.release()
        video_processor = VideoProcessor(video_source=new_source)
        return video_processor, new_source
    return video_processor, current_source
