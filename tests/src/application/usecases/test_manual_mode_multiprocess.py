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


def test_manual_process_publishes_frame_when_enabled():
    shared_controls = {"MANUAL_MD": True, "LANE_SOURCE_TAB2": "cam"}
    shared_frames = {}
    lane_queue = queue.Queue()
    video_proc = MagicMock()
    video_proc.get_frame.return_value = "frame"

    def publish_side_effect(**kwargs):
        shared_controls["MANUAL_MD"] = False

    with patch("src.application.usecases.manual_mode_multiprocess.switch_video_source", return_value=(video_proc, "cam")) as mock_switch, \
         patch("src.application.usecases.manual_mode_multiprocess.update_processing_time", return_value=(0, 0, 0, 0)), \
         patch("src.application.usecases.manual_mode_multiprocess.publish", side_effect=publish_side_effect) as mock_publish, \
         patch("src.application.usecases.manual_mode_multiprocess.Logger"):
        manual_video_process(shared_controls, shared_frames, lane_queue)

    mock_switch.assert_called_once()
    video_proc.get_frame.assert_called_once()
    assert mock_publish.call_args.kwargs["frame"] == "frame"

