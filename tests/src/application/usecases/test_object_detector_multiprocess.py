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


def test_object_detector_processes_frame_and_puts_data():
    object_queue = MagicMock()
    object_queue.full.return_value = False
    shared_controls = {"RUNNING": True, "OBJECT_SERIAL_DATA": [0, 0, 0]}
    shared_frames = {}
    tk_controls = {}
    video_proc = MagicMock()

    def capture_side_effect(**kwargs):
        shared_controls["RUNNING"] = False
        return video_proc, "frame"

    object_detector_mock = MagicMock()
    object_detector_mock.video_processor = video_proc

    with patch("src.application.usecases.object_detector_multiprocess.set_process_priority"), \
         patch("src.application.usecases.object_detector_multiprocess.open_video_source", return_value=video_proc), \
         patch("src.application.usecases.object_detector_multiprocess.ObjectDetector", return_value=object_detector_mock), \
         patch("src.application.usecases.object_detector_multiprocess.capture_frame_with_reopen", side_effect=capture_side_effect), \
         patch("src.application.usecases.object_detector_multiprocess.switch_video_source", return_value=(video_proc, None)), \
         patch("src.application.usecases.object_detector_multiprocess.Logger"):
        object_detection_process(object_queue, shared_controls, shared_frames, tk_controls, verbose=False)

    object_detector_mock.process_frame.assert_called_once_with("frame")
    object_queue.put.assert_called_once_with({"OBJECT_PERSON_DATA": 0, "TRAFFIC_LIGHT_DATA": 0})

