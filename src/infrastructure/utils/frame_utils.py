import io
from typing import Union

import cv2 as cv
import numpy as np
from PIL import Image


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

def _camera_safe_stop(_, shared_controls, logger, reason="CAMERA_ERROR"):
    shared_controls["SAFE_STOP"] = True
    logger.warning(f"SAFE-STOP ativado ({reason}).")