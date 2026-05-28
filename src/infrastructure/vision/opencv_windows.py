import cv2 as cv
import numpy as np

from src.infrastructure.media.frame_codec import encode_frame


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
    cv.putText(
        img,
        "Carregando Detector...",
        (50, 135),
        cv.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )
    return encode_frame(img)
