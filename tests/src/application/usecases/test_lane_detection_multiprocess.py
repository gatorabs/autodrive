import queue
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
