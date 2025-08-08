import io
from typing import Union

import cv2
import numpy as np
from PIL import Image


def encode_frame(frame: Union[np.ndarray, bytes, bytearray]) -> bytes:
    """Encode frame into JPEG bytes using PIL for stability.

    Accepts frames as numpy arrays (BGR) or raw bytes. If the frame is already
    bytes, it is returned unchanged.
    """
    if isinstance(frame, (bytes, bytearray)):
        return bytes(frame)
    if isinstance(frame, np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue()
    raise TypeError("Frame must be a numpy array or bytes")
