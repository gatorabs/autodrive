import cv2
import contextlib
import os
import glob
from src.infrastructure.constants.colorsConstants import RED, YELLOW, GREEN, RESET

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
        print(f"{YELLOW}[FLAGS]{RESET}{RED}[WARNING] Nenhuma câmera foi detectada.{RESET}")
    elif qtd == 1:
        print(f"{YELLOW}[FLAGS]{RESET}{GREEN}[INFO] Câmera detectada:{RESET} (índice {available[0]}).")
    else:
        print(f"{YELLOW}[FLAGS]{RESET}{GREEN}[INFO] Câmeras detectadas:{RESET} (índices {', '.join(available)})")
    return available

def get_video_files_from_folder(folder="resources/test_videos"):
    video_exts = ("*.mp4", "*.avi", "*.mov", "*.mkv")
    files = []
    for ext in video_exts:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(files)
