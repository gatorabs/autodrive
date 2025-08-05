import cv2
import contextlib
import os
import glob
from src.infrastructure.logging.logger import Logger

logger = Logger("FLAGS", verbose=True)


def detect_camera_indices(max_tested=2, exclude_indices=None):
    """Detect available camera indices.

    Parameters
    ----------
    max_tested : int
        Number of camera indices to test, not counting excluded ones.
    exclude_indices : list[int | str] | None
        Camera indices that should be ignored during detection. Useful when a
        camera is already in use elsewhere and should not be probed again.
    """

    exclude_set = {str(i) for i in (exclude_indices or [])}
    available = []

    # test additional indices so that `max_tested` usable cameras are checked
    for i in range(max_tested + len(exclude_set)):
        if str(i) in exclude_set:
            continue
        with open(os.devnull, "w") as fnull, contextlib.redirect_stderr(fnull):
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
