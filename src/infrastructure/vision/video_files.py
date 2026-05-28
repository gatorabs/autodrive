import glob
import os

from src.infrastructure.constants.path_constants import TEST_VIDEOS_DIR


def get_video_files_from_folder(folder=TEST_VIDEOS_DIR):
    video_exts = ("*.mp4", "*.avi", "*.mov", "*.mkv")
    files = []
    folder = os.fspath(folder)
    for ext in video_exts:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(files)
