import queue
from unittest.mock import patch, MagicMock

from src.application.usecases.manual_mode_multiprocess import manual_video_process


def test_manual_process_exits_when_disabled():
    shared_controls = {"MANUAL_MD": False}
    shared_frames = {}
    lane_queue = queue.Queue()

    with patch("src.application.usecases.manual_mode_multiprocess.switch_video_source") as mock_switch:
        manual_video_process(shared_controls, shared_frames, lane_queue)

    mock_switch.assert_not_called()

