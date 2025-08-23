import queue
from unittest.mock import MagicMock, patch

from src.application.usecases.data_sender_multiprocess import data_sender_process


def test_data_sender_initializes_serial_and_sets_priority():
    lane_queue = queue.Queue()
    object_queue = queue.Queue()
    shared_controls = {"RUNNING": False, "SENDER_COM": "COM1"}
    tk_controls = {}

    with patch("src.application.usecases.data_sender_multiprocess.set_process_priority") as mock_prio, \
         patch("src.application.usecases.data_sender_multiprocess.SerialCommunicator", return_value=MagicMock()) as mock_serial, \
         patch("src.application.usecases.data_sender_multiprocess.Logger"):
        data_sender_process(lane_queue, object_queue, shared_controls, tk_controls, verbose=False)

    mock_prio.assert_called_once_with("high")
    assert mock_serial.call_args.kwargs["com_port"] == "COM1"
    assert mock_serial.call_args.kwargs["send_data"] is False


def test_data_sender_publishes_lane_data_from_queue():
    lane_queue = queue.Queue()
    lane_queue.put({"CAR_SPEED_DATA": 100})
    object_queue = queue.Queue()
    shared_controls = {
        "RUNNING": True,
        "SENDER_COM": "COM1",
        "SEND_DATA": False,
        "MANUAL_MD": False,
    }
    tk_controls = {"SEND_LOGS": False}

    serial_mock = MagicMock()

    def publish_side_effect(**kwargs):
        shared_controls["RUNNING"] = False

    with patch("src.application.usecases.data_sender_multiprocess.set_process_priority"), \
         patch("src.application.usecases.data_sender_multiprocess.SerialCommunicator", return_value=serial_mock), \
         patch("src.application.usecases.data_sender_multiprocess.switch_serial_com", return_value=(serial_mock, "COM1")), \
         patch("src.application.usecases.data_sender_multiprocess.handle_object_queue"), \
         patch("src.application.usecases.data_sender_multiprocess.publish_emergency_stop"), \
         patch("src.application.usecases.data_sender_multiprocess.publish", side_effect=publish_side_effect) as mock_publish, \
         patch("src.application.usecases.data_sender_multiprocess.time.monotonic", side_effect=[0, 0]), \
         patch("src.application.usecases.data_sender_multiprocess.Logger"):
        data_sender_process(lane_queue, object_queue, shared_controls, tk_controls, verbose=False)

    mock_publish.assert_called_once()
    assert mock_publish.call_args.kwargs["lane_data"]["CAR_SPEED_DATA"] == 100

