import cv2
import contextlib
import os
import glob
from src.infrastructure.logging.logger import Logger

logger = Logger("FLAGS", verbose=True)

def detect_camera_indices(max_tested=2):
    available = []
    for i in range(max_tested):
        with open(os.devnull, 'w') as fnull, contextlib.redirect_stderr(fnull):
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.read()[0]:
                available.append(str(i))
            cap.release()

    qtd = len(available)
    if qtd == 0:
        logger.error(f"Nenhuma câmera foi detectada.")
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
