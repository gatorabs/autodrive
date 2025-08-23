import queue
import cv2 as cv
from unittest.mock import MagicMock, patch

from src.application.usecases.lane_detection_multiprocess import lane_detection_process


def test_lane_detection_sets_priority_and_opens_video():
    lane_queue = queue.Queue()
    shared_controls = {"RUNNING": False}
    shared_frames = {}
    tk_controls = {}

    with patch("src.application.usecases.lane_detection_multiprocess.set_process_priority") as mock_prio, \
         patch("src.application.usecases.lane_detection_multiprocess.open_video_source", return_value=MagicMock()) as mock_open, \
         patch("src.application.usecases.lane_detection_multiprocess.pid_setup", return_value=None), \
         patch("src.application.usecases.lane_detection_multiprocess.cv.getStructuringElement", return_value=None), \
         patch("src.application.usecases.lane_detection_multiprocess.cv.destroyAllWindows"), \
         patch("src.application.usecases.lane_detection_multiprocess.Logger"):
        lane_detection_process(lane_queue, shared_controls, shared_frames, tk_controls, verbose=False)

    mock_prio.assert_called_once_with("above_normal")
    mock_open.assert_called_once()


def test_lane_detection_logs_error_on_preprocess_exception():
    lane_queue = queue.Queue()
    shared_controls = {"RUNNING": True}
    shared_frames = {}
    tk_controls = {}
    video_proc = MagicMock()

    def mock_preprocess(frame, tk_controls, morph_kernel):
        shared_controls["RUNNING"] = False
        raise cv.error("boom")

    with patch("src.application.usecases.lane_detection_multiprocess.set_process_priority"), \
         patch("src.application.usecases.lane_detection_multiprocess.open_video_source", return_value=video_proc), \
         patch("src.application.usecases.lane_detection_multiprocess.capture_frame_with_reopen", return_value=(video_proc, MagicMock())), \
         patch("src.application.usecases.lane_detection_multiprocess.preprocess", side_effect=mock_preprocess), \
         patch("src.application.usecases.lane_detection_multiprocess.cv.getStructuringElement", return_value=None), \
         patch("src.application.usecases.lane_detection_multiprocess.cv.destroyAllWindows"), \
         patch("src.application.usecases.lane_detection_multiprocess.pid_setup", return_value=None), \
         patch("src.application.usecases.lane_detection_multiprocess.Logger") as mock_logger:
        lane_detection_process(lane_queue, shared_controls, shared_frames, tk_controls, verbose=False)

    mock_logger.return_value.error.assert_called()
