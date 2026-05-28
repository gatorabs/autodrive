import contextlib
import os

import cv2 as cv

from src.infrastructure.logging.logger import Logger

logger = Logger("FLAGS", verbose=True)


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
        logger.error("Nenhuma camera foi detectada.")
    elif qtd == 1:
        logger.info(f"Camera detectada: (indice {available[0]}).")
    else:
        logger.info(f"Cameras detectadas: (indices {', '.join(available)})")
    return available
