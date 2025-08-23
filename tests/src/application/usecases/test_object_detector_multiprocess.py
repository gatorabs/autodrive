import queue
from unittest.mock import MagicMock, patch

from src.application.usecases.object_detector_multiprocess import object_detection_process


def test_object_detector_sets_priority_and_opens_video():
    object_queue = queue.Queue()
    shared_controls = {"RUNNING": False, "OBJECT_SERIAL_DATA": [0, 0, 0]}
    shared_frames = {}
    tk_controls = {}

    with patch("src.application.usecases.object_detector_multiprocess.set_process_priority") as mock_prio, \
         patch("src.application.usecases.object_detector_multiprocess.open_video_source", return_value=MagicMock()) as mock_open, \
         patch("src.application.usecases.object_detector_multiprocess.ObjectDetector", return_value=MagicMock()) as mock_detector, \
         patch("src.application.usecases.object_detector_multiprocess.Logger"):
        object_detection_process(object_queue, shared_controls, shared_frames, tk_controls, verbose=False)

    mock_prio.assert_called_once_with("high")
    mock_open.assert_called_once()
    mock_detector.assert_called_once()

