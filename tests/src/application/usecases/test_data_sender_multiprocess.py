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

